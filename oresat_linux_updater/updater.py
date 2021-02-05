"""Linux updater daemon"""

import json
import logging
import tarfile
from time import sleep
from os import listdir
from os.path import abspath, basename
from shutil import copyfile, move, rmtree
from pathlib import Path
from enum import IntEnum, auto
from threading import Thread, Lock
from pydbus.generic import signal
from oresat_linux_updater.olm_file import OLMFile
from oresat_linux_updater.status_archive import make_status_archive
from oresat_linux_updater.update_archive import extract_update_archive, \
        is_update_archive, UpdateError, InstructionError


DBUS_INTERFACE_NAME = "org.oresat.updater"


class State(IntEnum):
    """The states oresat linux updaer daemon can be in."""

    STANDBY = 0
    """Waiting for commands."""

    UPDATE = auto()
    """Updating."""

    STATUS_FILE = auto()
    """Making the status tar file."""


class Result(IntEnum):
    """The integer value UpdateResult will return"""

    NOTHING = 0
    """Nothing for the updater to do. The cache was empty."""

    SUCCESS = auto()
    """The update successfully install."""

    FAILED_NON_CRIT = auto()
    """The update failed during the inital non critical section. Either the was
    an error using the file cache, when opening tarfile, or reading the
    instructions file.
    """

    FAILED_CRIT = auto()
    """The update failed during the critical section. The updater fail while
    following the instructions.
    """


class Updater():
    """The oresat linux updater. All D-Bus methods, properties, and signals
    follow Pascal case naming.
    """

    dbus = """
    <node>
        <interface name="org.oresat.updater">
            <method name='AddUpdateArchive'>
                <arg type='s' name='update_archive' direction='in'/>
                <arg type='b' name='output' direction='out'/>
            </method>
            <method name='Update'>
                <arg type='b' name='output' direction='out'/>
            </method>
            <method name='MakeStatusArchive'>
                <arg type='b' name='output' direction='out'/>
            </method>
            <property name="StatusName" type="s" access="read" />
            <property name="StatusValue" type="y" access="read" />
            <property name="UpdateArchive" type="s" access="read" />
            <property name="AvailableUpdateArchives" type="u" access="read" />
            <signal name="StatusArchive">
                <arg type='s'/>
            </signal>
            <signal name="UpdateResult">
                <arg type='y'/>
            </signal>
        </interface>
    </node>
    """  # doesn't work in __init__()

    # dbus signals
    StatusArchive = signal()
    UpdateResult = signal()

    # -------------------------------------------------------------------------
    # non-dbus methods

    def __init__(self,
                 work_dir: str,
                 cache_dir: str,
                 logger: logging.Logger
                 ):
        """
        Parameters
        ----------
        work_dir: str
            Archivepath to working directory.
        cache_dir: str
            Archivepath to update archive cache directory.
        logger: logging.Logger
            The logger object to use.

        Attributes
        ----------
        StatusArchive: str
            D-Bus signal with a str that will sent the absolute path to the
            updater status file after the MakeStatusArchive dbus method is
            called.
        UpdateResult: uint8
            D-Bus signal with a :class:`Result` value that will be sent after
            an update has finished or failed.
        """

        self._log = logger

        # make update_archives for cache dir
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        self._cache_dir = abspath(cache_dir) + "/"
        self._log.debug("cache dir " + self._cache_dir)
        self._cache = listdir(self._cache_dir)
        self._cache.sort(reverse=True)

        # make update_archives for work dir
        Path(work_dir).mkdir(parents=True, exist_ok=True)
        self._work_dir = abspath(work_dir) + "/"
        self._log.debug("work dir " + self._work_dir)

        self._status = State.STANDBY
        self._update_archive = ""
        self._lock = Lock()

        # set up working thread
        self._running = False
        self._working_thread = Thread(target=self._working_loop)

    def __del__(self):
        self.quit()

    def start(self):
        """Start the working thread."""
        self._log.debug("starting working thread")
        self._running = True
        self._working_thread.start()

    def quit(self):
        """Stop the working thread."""
        self._log.debug("stopping working thread")
        self._running = False
        if self._working_thread.is_alive():
            self._working_thread.join()

    def _working_loop(self):
        """The main loop to contol the Linux Updater asynchronously. Will be in
        its own thread.
        """

        if len(listdir(self._work_dir)) != 0:
            self._log.info("Files found in work dir, tring to resume update")
            ret = self._update(True)  # need to resume
            self.UpdateResult(ret)

        self._log.debug("starting working loop")

        while self._running:
            if self._status == State.UPDATE:
                ret = self._update()
                self.UpdateResult(ret)
            elif self._status == State.STATUS_FILE:
                ret = make_status_archive(self._cache_dir, True)
                self.StatusArchive(ret)
            else:
                sleep(0.1)  # nothing for this thread to do

        self._log.debug("stoping working loop")

    def _update(self, resume=False) -> int:
        """Run a update. If the update fails, the cache will be cleared, as it
        is asume all newwer updates require the failed updated to be run
        successfully first.

        Parameters
        ----------
        resume: bool
            A flag for resuming update. If set to True, the it will try to find
            a update archive in work dir. Otherwise if set to False, it will
            try to get a update archive from the cache.

        Returns
        -------
        int
            A Result value.
        """

        ret = Result.SUCCESS
        update_archive = ""

        if resume:  # find update archive in work directory
            for fname in listdir(self._work_dir):
                if is_update_archive(fname):
                    update_archive = self._work_dir + fname
                    self._log.info("resuming update with " + fname)
                    break
        elif len(self._cache) != 0:  # get new update archive from cache
            print(self._cache)
            update_archive = \
                move(self._cache_dir + self._cache.pop(), self._work_dir)
            self._log.info("got " + basename(update_archive) + " from cache")

        if update_archive == "":  # nothing to do
            ret = Result.NOTHING

        # if there is a update archive to use, open it
        if ret == Result.SUCCESS:
            self._update_archive = basename(update_archive)
            self._log.info("starting update with " + self._update_archive)
            try:
                inst_list = extract_update_archive(update_archive, self._work_dir)
                self._log.debug(self._update_archive + " successfully opened")
            except (UpdateError, InstructionError, FileNotFoundError) as exc:
                self._log.critical(exc)
                ret = Result.FAILED_NON_CRIT

        # if update archive opened successfully, run the update
        if ret == Result.SUCCESS:
            try:
                for inst in inst_list:
                    inst.run(self._log)
                self._log.debug(self._update_archive + " successfully ran")
            except (UpdateError, InstructionError, FileNotFoundError) as exc:
                self._log.critical(exc)
                ret = Result.FAILED_CRIT

        if ret in [Result.FAILED_NON_CRIT, Result.FAILED_CRIT]:
            # update failed
            self._log.info("clearing file cache due to failed update")

            files = ""
            for i in self._cache:
                files += basename(i) + " "
            self._log.info("deleted " + files)

            rmtree(self._cache_dir, ignore_errors=True)
            Path(self._cache_dir).mkdir(parents=True, exist_ok=True)
            self._cache = []

        self._clear_work_dir()
        self._update_archive = ""
        self._log.info("update {} result {}".format(self._update_archive, ret))
        self._status = State.STANDBY
        return ret

    def _clear_work_dir(self):
        """Clears the working directory."""
        if len(listdir(self._work_dir)) != 0:
            rmtree(self._work_dir, ignore_errors=True)
            Path(self._work_dir).mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # dbus properties

    @property
    def StatusName(self) -> str:
        """str: D-Bus property for the curent status as a :class:`State`
        name. Readonly.
        """
        return self._status.value

    @property
    def StatusValue(self) -> int:
        """uint8: D-Bus property for the curent status as a :class:`State`
        value. Readonly.
        """
        return self._status.value

    @property
    def AvailableUpdateArchives(self) -> int:
        """uint32: D-Bus property for the number of update archives in cache.
        Readonly.
        """
        return len(self._cache)

    @property
    def UpdateArchive(self) -> str:
        """str: D-Bus property for the current update archive. Will be a empty
        str if the daemon is not currently updating. Readonly.
        """
        return self._update

    # -------------------------------------------------------------------------
    # dbus methods

    def AddUpdateArchive(self, update_archive: str) -> bool:
        """D-Bus method that copies an update archive into the update archive cache.

        Parameters
        ----------
        update_archive: str
            The absolute path to update archive for the updater to store.

        Returns
        -------
        bool
            True if a file was added or False on failure.
        """

        ret = True
        filename = basename(update_archive)

        try:
            OLMFile(load=update_archive)
            copyfile(update_archive, self._cache_dir + filename)
            self._cache.append(filename)
            self._cache.sort(reverse=True)
            self._log.info(filename + " was added to cache")
        except Exception:
            self._log.error(filename + " is a invalid filename")
            ret = False

        return ret

    def Update(self) -> bool:
        """D-Bus method to load the oldest update archive in cache and runs update.

        Returns
        -------
        bool
            True if a the updater will start to update or False on failure.
        """

        ret = False
        self._lock.acquire()

        if self._status == State.STANDBY:
            self._status = State.UPDATE
            ret = True

        self._lock.release()
        return ret

    def MakeStatusArchive(self) -> bool:
        """D-Bus method to make status tar file with a copy of the dpkg status
        file and a file with the list of update archives in cache. Will
        asynchronously reply with the StatusArchive dbus signal with the path
        to the file once the file is made.

        Returns
        -------
        bool
            True if a the updater will make the status tar or False on failure.
        """

        ret = False
        self._lock.acquire()

        if self._status == State.STANDBY:
            self._status = State.STATUS_FILE
            ret = True

        self._lock.release()
        return ret

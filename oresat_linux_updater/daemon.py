"""Linux updater daemon"""

import logging
import tarfile
import json
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
from oresat_linux_updater.update import extract_update_file, is_update_file, \
        UpdateError, InstructionError


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


class Daemon():
    """The class for the oresat linux updater daemon. All D-Bus methods,
    properties, and signals follow Pascal case naming.
    """

    dbus = """
    <node>
        <interface name="org.oresat.updater">
            <method name='AddUpdateFile'>
                <arg type='s' name='update_file' direction='in'/>
                <arg type='b' name='output' direction='out'/>
            </method>
            <method name='Update'>
                <arg type='b' name='output' direction='out'/>
            </method>
            <method name='MakeStatusFile'>
                <arg type='b' name='output' direction='out'/>
            </method>
            <property name="StatusName" type="s" access="read" />
            <property name="StatusValue" type="y" access="read" />
            <property name="UpdateFile" type="s" access="read" />
            <property name="AvailableUpdateFiles" type="u" access="read" />
            <signal name="StatusFile">
                <arg type='s'/>
            </signal>
            <signal name="UpdateResult">
                <arg type='y'/>
            </signal>
        </interface>
    </node>
    """  # doesn't work in __init__()

    # dbus signals
    StatusFile = signal()
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
            Filepath to working directory.
        cache_dir: str
            Filepath to update file cache directory.
        logger: logging.Logger
            The logger object to use.

        Attributes
        ----------
        StatusFile: str
            D-Bus signal with a str that will sent the absolute path to the
            updater status file after the MakeStatusFile dbus method is called.
        UpdateResult: uint8
            D-Bus signal with a :class:`Result` value that will be sent after
            an update has finished or failed.
        """

        self._log = logger

        # make update_files for cache dir
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        self._cache_dir = abspath(cache_dir) + "/"
        self._log.debug("cache dir " + self._cache_dir)
        self._cache = listdir(self._cache_dir)
        self._cache.sort(reverse=True)

        # make update_files for work dir
        Path(work_dir).mkdir(parents=True, exist_ok=True)
        self._work_dir = abspath(work_dir) + "/"
        self._log.debug("work dir " + self._work_dir)

        self._status = State.STANDBY
        self._update_file = ""
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
                self.StatusFile(ret)
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
            a update file in work dir. Otherwise if set to False, it will try
            to get a update file from the cache.

        Returns
        -------
        int
            A Result value.
        """

        ret = Result.SUCCESS
        update_file = ""

        if resume:  # find update file in work directory
            for f in listdir(self._work_dir):
                if is_update_file(f):
                    update_file = self._work_dir + f
                    self._log.info("resuming update with " + f)
                    break
        elif len(self._cache) != 0:  # get new update file from cache
            print(self._cache)
            update_file = \
                move(self._cache_dir + self._cache.pop(), self._work_dir)
            self._log.info("got " + basename(update_file) + " from cache")

        if update_file == "":  # nothing to do
            ret = Result.NOTHING

        # if there is a update file to use, open it
        if ret == Result.SUCCESS:
            self._update_file = basename(update_file)
            self._log.info("starting update with " + self._update_file)
            try:
                inst_list = extract_update_file(update_file, self._work_dir)
                self._log.debug(self._update_file + " successfully opened")
            except (UpdateError, InstructionError, FileNotFoundError) as exc:
                self._log.critical(exc)
                ret = Result.FAILED_NON_CRIT

        # if update file opened successfully, run the update
        if ret == Result.SUCCESS:
            try:
                for inst in inst_list:
                    inst.run(self._log)
                self._log.debug(self._update_file + " successfully ran")
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
        self._update_file = ""
        self._log.info("update {} result {}".format(self._update_file, ret))
        self._status = State.STANDBY
        return ret

    def _make_status_file(self) -> str:
        """Make status tar file with a copy of the dpkg status file and a file
        with the list of updates in cache.

        Returns
        -------
        str
            Path to new status file or empty string on failure.
        """

        dpkg_file = OLMFile(keyword="dpkg-status").name
        olu_file = self._work_dir + OLMFile(keyword="olu-status").name
        olu_tar = "/tmp/" + OLMFile(keyword="olu-status", ext=".tar.xz").name

        with open(olu_file, "w") as fptr:
            fptr.write(json.dumps(listdir(self._cache_dir)))

        with tarfile.open(olu_tar, "w:xz") as tfptr:
            tfptr.add("/var/lib/dpkg/status", arcname=basename(dpkg_file))
            tfptr.add(olu_file, arcname=basename(olu_file))

        self._clear_work_dir()
        self._status = State.STANDBY
        return olu_tar

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
    def AvailableUpdateFiles(self) -> int:
        """uint32: D-Bus property for the number of update files in cache.
        Readonly.
        """
        return len(self._cache)

    @property
    def UpdateFile(self) -> str:
        """str: D-Bus property for the current update file. Will be a empty
        str if the daemon is not currently updating. Readonly.
        """
        return self._update

    # -------------------------------------------------------------------------
    # dbus methods

    def AddUpdateFile(self, update_file: str) -> bool:
        """D-Bus method that copies an update file into the update file cache.

        Parameters
        ----------
        update_file: str
            The absolute path to update file for the updater to store.

        Returns
        -------
        bool
            True if a file was added or False on failure.
        """

        ret = True
        filename = basename(update_file)

        try:
            OLMFile(load=update_file)
            copyfile(update_file, self._cache_dir + filename)
            self._cache.append(filename)
            self._cache.sort(reverse=True)
            self._log.info(filename + " was added to cache")
        except Exception:
            self._log.error(filename + " is a invalid filename")
            ret = False

        return ret

    def Update(self) -> bool:
        """D-Bus method to load the oldest update file in cache and runs update.

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

    def MakeStatusFile(self) -> bool:
        """D-Bus method to make status tar file with a copy of the dpkg status
        file and a file with the list of update files in cache. Will
        asynchronously reply with the StatusFile dbus signal with the path to
        the file once the file is made.

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

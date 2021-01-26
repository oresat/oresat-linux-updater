"""Linux updater daemon"""

import threading
import time
import logging
import subprocess
import tarfile
from datetime import datetime
from os import remove, uname
from os.path import basename
from pathlib import Path
from enum import IntEnum, auto
from pydbus.generic import signal
from oresat_linux_updater import INST_FILE
from oresat_linux_updater.file_cache import FileCache
from oresat_linux_updater.instructions_list import InstructionsList, \
        InstructionType, InstructionsTxtError


DBUS_INTERFACE_NAME = "org.oresat.updater"


class State(IntEnum):
    """The states oresat linux updaer daemon can be in."""

    STANDBY = auto()
    """Waiting for commands."""

    UPDATE = auto()
    """Updating."""

    STATUS_FILE = auto()
    """Making the status tar file."""


class Result(IntEnum):
    """The integer value UpdateResult will return"""

    NOTHING = auto()
    """Nothing for the updater to do. The cache was empty."""

    SUCCESS = auto()
    """The update successfully install."""

    FAILED_NON_CRIT = auto()
    """The update failed during the inital non critical section. Either the was
    an error using the file cache, when opening tarfile, or readng
    instructions.txt
    """

    FAILED_CRIT = auto()
    """The update failed during the critical section. The updater fail while
    following the instructions.
    """


class UpdaterDaemon():
    """The class for the oresat linux updater daemon."""

    dbus = """
    <node>
        <interface name="org.oresat.updater">
            <method name='AddArchiveFile'>
                <arg type='s' name='filepath' direction='in'/>
                <arg type='b' name='output' direction='out'/>
            </method>
            <method name='Update'>
                <arg type='b' name='output' direction='out'/>
            </method>
            <method name='MakeStatusFile'>
                <arg type='b' name='output' direction='out'/>
            </method>
            <property name="Status" type="s" access="read" />
            <property name="ArchiveFile" type="s" access="read" />
            <property name="AvailableArchiveFiles" type="d" access="read" />
            <signal name="StatusFile">
                <arg type='s'/>
            </signal>
            <signal name="UpdateResult">
                <arg type='b'/>
            </signal>
        </interface>
    </node>
    """

    # dbus signals
    StatusFile = signal()
    UpdateResult = signal()

    # -------------------------------------------------------------------------
    # non-dbus methods

    def __init__(self,
                 working_dir: str,
                 file_cache_dir: str,
                 logger: logging.Logger
                 ):
        """
        Parameters
        ----------
        working_dir: str
            Filepath to working directory.
        file_cache_dir: str
            Filepath to file cache directory.
        logger: logging.Logger
            The logger object to use.

        Attributes
        ----------
        StatusFile: str
            Dbus signal with a str that will sent the absolute path to the
            updater status file after the MakeStatusFile dbus method is called.
        UpdateResult: uint8
            Dbus signal with a bool that will be sent after an update has
            finished. True if the update was a successful or False if the
            update failed.

        """

        # make filepaths for cache dir
        if file_cache_dir[-1] != "/":
            file_cache_dir += "/"
        self._cache_dir_path = file_cache_dir + "oresat_linux_updater/"
        Path(self._cache_dir_path).mkdir(parents=True, exist_ok=True)

        self._log = logger
        self._file_cache = FileCache(self._cache_dir_path)
        self._work_dir = working_dir
        self._status = State.STANDBY
        self._archive_file = ""

        self._log.debug("cache " + self._cache_dir_path)
        self._log.debug("cache " + working_dir)

        # set up working thread
        self._working_thread = threading.Thread(target=self._working_loop)

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
        """
        The main loop to contol the Linux Updater asynchronously. Will be in
        its own thread.
        """

        self._log.debug("starting working loop")

        while self._running:
            if self._status == State.UPDATE:
                ret = self._update()
                self.UpdateResult(ret)
                self._status = State.STANDBY
            elif self._status == State.STATUS_FILE:
                ret = self._make_status_file()
                self.StatusFile(ret)
                self._status = State.STANDBY
            else:
                time.sleep(0.1)  # nothing for this thread to do

        self._log.debug("stoping working loop")

    def _update(self) -> bool:
        """Runs the update. Archive file should be in working directory.

        Returns
        -------
        bool
            True if the update worked or if there was no update archives. False
            on failure.
        """

        ret = True

        # get new archive file from cache
        archive_file = self._file_cache.get(self._work_dir)

        if not archive_file:
            self._log.info("no files in cache")
            return True  # no files, nothing to do

        self._archive_file = basename(archive_file)

        self._log.info("starting update with " + archive_file)

        with tarfile.open(archive_file, "r:xz") as tfile:
            self._log.debug("untar " + archive_file)
            tfile.extractall(path=self._work_dir)

        try:
            instructions = InstructionsList(self._work_dir + INST_FILE)
        except (InstructionsTxtError, FileNotFoundError) as exc:
            self._log.error(exc)
            self._archive_file = ""
            return False

        self._log.info("no turn back point")
        """
        No turn back point, the update is starting!!!
        If anything fails/errors the board's software could break.
        All fails/errors are log at critical level.
        """

        for i in instructions:
            if i.type == InstructionType.BASH_SCRIPT.name:
                for item in i.items:
                    command = "bash -c " + item
                    ret = self._bash_command(command)
                    if ret is False:
                        break
            elif i.type == InstructionType.DPKG_INSTALL.name:
                command = "dpkg -i"
                for pkg in i.items:
                    command += " " + self._work_dir + pkg
                ret = self._bash_command(command)
            elif i.type == InstructionType.DPKG_REMOVE.name:
                command = "dpkg -r"
                for pkg in i.items:
                    command += " " + pkg
                ret = self._bash_command(command)
            elif i.type == InstructionType.DPKG_PURGE.name:
                command = "dpkg -P"
                for pkg in i.items:
                    command += " " + pkg
                ret = self._bash_command(command)
            else:
                self._log.critical("Unknown instruction type " + i.type)
                ret = False
                break

            if ret is False:
                self._log.critical("update failed")
                break

        self._archive_file = ""
        return ret

    def _bash_command(self, command: str) -> bool:
        """Run a bash command. All stdout message will be logged with info
        level and all stderr messages will be logged with error level.

        Parameters
        ----------
        commnad : str
            The bash command string to run.
        logger: Logger
            The logger to use for to log with for stderr and stderr streams.

        Returns
        -------
        bool
            True on successful or False on failure.
        """

        ret = True

        self._log.info(command)

        out = subprocess.run(command, capture_output=True, shell=True)

        if out.returncode != 0:
            for line in out.stderr.decode("utf-8").split("\n"):
                if len(line) != 0:
                    self._log.info(line)
            ret = False

        for line in out.stdout.decode("utf-8").split("\n"):
            if len(line) != 0:
                self._log.info(line)

        return ret

    def _make_status_file(self) -> str:
        """Make status tar file with a copy of the dpkg status file and a file
        with the list of update archives in cache.

        Returns
        -------
        str
            The absolute path to the file made.
        """

        date_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        hostname = uname()[1]

        dpkg_file = self._work_dir + hostname + "_dpkg-status_" + date_str + ".txt"
        olu_file = self._work_dir + hostname + "_olu-status_" + date_str + ".txt"
        tar_file = "/tmp/" + hostname + "_olu-status_" + date_str + ".tar.xz"

        with open(olu_file, "w") as fptr:
            fptr.write(self._file_cache.json_str())

        with tarfile.open(tar_file, "w:xz") as tfptr:
            tfptr.add("/var/lib/dpkg/status", arcname=basename(dpkg_file))
            tfptr.add(olu_file, arcname=basename(olu_file))

        remove(olu_file)

        return tar_file

    # -------------------------------------------------------------------------
    # dbus properties

    @property
    def Status(self) -> str:
        """str: Dbus property for the curent state's name. Readonly."""
        return self._status.name

    @property
    def AvailableArchiveFiles(self) -> int:
        """int: Dbus property for the number of archive files in cache.
        Readonly.
        """
        return len(self._file_cache)

    @property
    def ArchiveFile(self) -> str:
        """str: Dbus property for the current archive file. Readonly."""
        return self._archive_file

    # -------------------------------------------------------------------------
    # dbus methods

    def AddArchiveFile(self, filepath: str) -> bool:
        """Dbus methof that copies an archive file into the update archive cache.

        Parameters
        ----------
        filepath: str
            The absolute path to archive file for the updater to store.

        Returns
        -------
        bool
            True if a file was added or False on failure.
        """

        try:
            self._file_cache.add(filepath)
            self._log.info(basename(filepath) + " was added to cache")
        except FileNotFoundError:
            self._log.error("failed to add " + basename(filepath) + " to cache")
            return False

        return True

    def Update(self) -> bool:
        """Dbus method to load the oldest archive file in cache and runs update.

        Returns
        -------
        bool
            True if a the updater will start to update or False on failure.
        """

        if self._status == State.STANDBY:
            self._status = State.UPDATE
            return True
        return False

    def MakeStatusFile(self) -> bool:
        """Dbus method to make status tar file with a copy of the dpkg status
        file and a file with the list of update archives in cache. Will
        asynchronously reply with the StatusFile dbus signal with the path to
        the file once the file is made.

        Returns
        -------
        bool
            True if a the updater will make the status tar or False on failure.
        """

        if self._status == State.STANDBY:
            self._status = State.STATUS_FILE
            return True
        return False

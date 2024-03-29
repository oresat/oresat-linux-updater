"""OreSat Linux updater D-Bus server"""

from logging import Logger
from time import sleep
from enum import IntEnum, auto
from threading import Thread, Lock
from pydbus.generic import signal
from oresat_linux_updater.status_archive import make_status_archive
from oresat_linux_updater.updater import Updater, Result


DBUS_INTERFACE_NAME = "org.OreSat.Updater"


class State(IntEnum):
    """The states oresat linux updaer daemon can be in."""

    STANDBY = 0
    """Waiting for commands."""

    UPDATE = auto()
    """Updating."""

    UPDATE_FAILED = auto()
    """Update failed, cache was cleared"""

    STATUS_FILE = auto()
    """Making the status tar file."""


class DBusServer():
    """The D-Bus Server wrapper ontop oresat linux updater that handles all
    threading.

    Note: all D-Bus Methods, Properties, and Signals follow Pascal case naming.
    """

    # D-Bus interface(s) definition
    dbus = """
    <node>
        <interface name="org.OreSat.Updater">
            <method name='AddUpdateArchive'>
                <arg type='s' name='update_archive' direction='in'/>
                <arg type='b' name='output' direction='out'/>
            </method>
            <method name='Update'>
                <arg type='b' name='output' direction='out'/>
            </method>
            <method name='MakeStatusArchive'>
                <arg type='s' name='filepath' direction='out'/>
            </method>
            <property name="StatusName" type="s" access="read" />
            <property name="StatusValue" type="y" access="read" />
            <property name="AvailableUpdateArchives" type="u" access="read" />
            <property name="ListUpdates" type="s" access="read" />
            <signal name="StatusArchive">
                <arg type='s'/>
            </signal>
            <signal name="UpdateResult">
                <arg type='y'/>
            </signal>
        </interface>
        <interface name="org.OreSat.Updater.Update">
            <property name="UpdateArchive" type="s" access="read" />
            <property name="TotalInstructions" type="y" access="read" />
            <property name="InstructionIndex" type="y" access="read" />
            <property name="InstructionCommand" type="s" access="read" />
        </interface>
    </node>
    """  # doesn't work in __init__()

    # -------------------------------------------------------------------------
    # D-Bus Signals

    # doesn't work in __init__()
    StatusArchive = signal()
    UpdateResult = signal()

    # -------------------------------------------------------------------------
    # non-D-Bus Methods

    def __init__(self, work_dir: str, cache_dir: str, logger: Logger):
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
            D-Bus Signal with a str that will sent the absolute path to the
            updater status file after the MakeStatusArchive D-Bus Method is
            called.
        UpdateResult: uint8
            D-Bus Signal with a :class:`Result` value that will be sent after
            an update has finished or failed.
        """

        self._log = logger
        self._updater = Updater(work_dir, cache_dir, logger)
        self._cache_dir = cache_dir

        self._status = State.STANDBY

        # set up working thread
        self._running = False
        self._working_thread = Thread(target=self._working_loop)
        self._mutex = Lock()

    def __del__(self):
        self.quit()

    def run(self):
        """Start the D-Bus server."""
        self._log.debug("starting working thread")
        self._running = True
        self._working_thread.start()

    def quit(self):
        """Stop the D-Bus server."""
        self._log.debug("stopping working thread")
        self._running = False
        if self._working_thread.is_alive():
            self._working_thread.join()

    def _working_loop(self):
        """The main loop to contol the Linux Updater asynchronously. Will be in
        its own thread.
        """

        self._log.debug("starting working loop")

        while self._running:
            if self._status == State.UPDATE:
                ret = self._updater.update()
                self.UpdateResult(ret)
                if ret in [Result.NOTHING, Result.SUCCESS]:
                    self._status = State.STANDBY
                else:
                    self._status = State.UPDATE_FAILED
            elif self._status in [State.STANDBY,
                                  State.STATUS_FILE,
                                  State.UPDATE_FAILED]:
                sleep(0.1)  # nothing for this thread to do
            else:  # this should not happen
                msg = "Invalid state in working loop {}".format(self._status)
                self._log.critical(msg)
                self._status = State.STANDBY

        self._log.debug("stoping working loop")

    # -------------------------------------------------------------------------
    # D-Bus Methods

    def AddUpdateArchive(self, update_archive: str) -> bool:
        """D-Bus Method that copies an update archive into the update archive cache.

        Parameters
        ----------
        update_archive: str
            The absolute path to update archive for the updater to store.

        Returns
        -------
        bool
            True if a file was added or False on failure.
        """

        return self._updater.add_update_archive(update_archive)

    def Update(self) -> bool:
        """D-Bus Method to load the oldest update archive in cache and runs update.

        Returns
        -------
        bool
            True if a the updater will start to update or False on failure.
        """

        ret = False

        self._mutex.acquire()
        if self._status in [State.STANDBY,
                            State.UPDATE_FAILED]:
            self._status = State.UPDATE
            ret = True
        self._mutex.release()

        return ret

    def MakeStatusArchive(self) -> str:
        """D-Bus Method to make status tar file with a copy of the dpkg status
        file and a file with the list of update archives in cache.

        Returns
        -------
        str
            Filepath to new file or empty str.
        """

        self._mutex.acquire()
        if self._status in [State.STANDBY,
                            State.UPDATE_FAILED]:
            self._status = State.STATUS_FILE
        self._mutex.release()

        self._log.debug("making status archive")
        ret = make_status_archive(self._cache_dir, True)

        if ret == "":
            self._log.critical("failed to make status archive")
        else:
            self._log.info(ret + " was made")

        self._mutex.acquire()
        self._status = State.STANDBY
        self._mutex.release()

        return ret

    # -------------------------------------------------------------------------
    # D-Bus Properties

    @property
    def StatusName(self) -> str:
        """str: D-Bus Property for the curent status as a :class:`State`
        name. Readonly.
        """

        return self._status.name

    @property
    def StatusValue(self) -> int:
        """uint8: D-Bus Property for the curent status as a :class:`State`
        value. Readonly.
        """

        return self._status.value

    @property
    def AvailableUpdateArchives(self) -> int:
        """uint32: D-Bus Property for the number of update archives in cache.
        Readonly.
        """

        return self._updater.available_update_archives

    @property
    def UpdateArchive(self) -> str:
        """str: D-Bus Property for the current update archive. Will be a empty
        str if the daemon is not currently updating. Readonly.
        """

        return self._updater.update_archive

    @property
    def ListUpdates(self) -> str:
        """str: D-Bus Property for get the list of update filename in the
        cache. Readonly.
        """

        return self._updater.list_updates

    @property
    def TotalInstructions(self) -> int:
        """uint8: D-Bus Property for the number intruction in the current
        update. Will be 0 if not updating. Readonly.
        """

        return self._updater.total_instructions

    @property
    def InstructionIndex(self) -> int:
        """uint8: D-Bus Property for current index in the instructions. Wil
        be 0 if not updating. Readonly.
        """

        return self._updater.instruction_index

    @property
    def InstructionCommand(self) -> str:
        """str: D-Bus Property for current instruction command. Will be an
        empty str if not updating. Readonly.
        """

        return self._updater.instruction_command

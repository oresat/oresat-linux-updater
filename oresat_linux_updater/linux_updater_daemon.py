"""Linux updater daemon"""

import threading
import time
import os
import logging
from enum import Enum
from pydbus.generic import signal
from oresat_linux_updater.linux_updater import LinuxUpdater

DBUS_INTERFACE_NAME = "org.oresat.updater"


class State(Enum):
    """
    All states for linux updater daemon,
    do NOT uses auto() since we DO care about the values.

    Parameters
    ----------
    failed
        Something failed, see logs.
    standby
        Waiting for commands.
    update
        Updating using an archive file.
    """
    failed = 0
    standby = 1
    update = 2


class LinuxUpdaterDaemon(object):
    """
    The daemon wrapper for the Linux updater. Includes a Dbus server, state
    machine, and logger ontop the linux_updater. Sets up two threads, one for
    the dbus server and one for the Linux updater. Having two threads allow
    commands to the daemon to handle asynchronously.

    Parameters
    ----------
    working_dir: str
        Filepath to working directory.
    file_cache_dir: str
        Filepath to file cache directory.
    """

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
            <method name='MakePackageListFile'>
                <arg type='b' name='output' direction='out'/>
            </method>
            <property name="CurrentStateName" type="s" access="read" />
            <property name="CurrentStateValue" type="d" access="read" />
            <property name="CurrentArchiveFile" type="s" access="read" />
            <property name="CurrentInstructionType" type="s" access="read" />
            <property name="CurrentInstructionItem" type="s" access="read" />
            <property name="AvailableArchiveFiles" type="d" access="read" />
            <signal name="PackageListFile">
                <arg type='s'/>
            </signal>
        </interface>
    </node>
    """

    PackageListFile = signal()

    # -------------------------------------------------------------------------
    # non-dbus methods

    def __init__(self,
                 working_dir=".",
                 file_cache_dir="./filecache/"
                 ):

        self._updater = LinuxUpdater(working_dir, file_cache_dir)

        # A flag for making a txt file with a list of all packages installed
        self._make_pkg_list = False

        # initial state machine
        if not os.listdir(working_dir):
            # somthing is in working dir, assume to resume update
            self._current_state = State.update
        else:
            self._current_state = State.standby

        logging.debug("init state is " + State.standby.name)

        self._state_transistions = {
            State.failed: [State.failed, State.standby],
            State.standby: [State.standby, State.update],
            State.update: [State.failed, State.standby, State.update]
            }

        # thread set up and start working thread
        self._lock = threading.Lock()
        self._working_thread = threading.Thread(target=self._working_loop)
        logging.debug("starting working thread")
        self._running = True
        self._working_thread.start()

    def __del__(self):
        # stop working thread
        self._running = False
        if self._working_thread.is_alive():
            self._working_thread.join()

    def _working_loop(self):
        """
        The main loop to contol the Linux Updater asynchronously. Will be in
        its own thread.
        """

        while self._running:
            if self._current_state != State.update and self._make_pkg_list:
                filepath = self._updater.get_pkg_list_file()
                self.PackageListFile(filepath)
                self._make_pkg_list = False
                continue
            elif self._current_state == State.standby:
                time.sleep(1)  # nothing for this thread to do
            elif self._current_state == State.update:
                ret = self._updater.update()
                if ret:
                    self._change_state(State.standby)
                else:
                    self._change_state(State.failed)
            else:  # should not happen
                logging.error("unknown state in working loop")
                self._change_state(State.failed)

    def _change_state(self, new_state: State) -> bool:
        """
        Change the daemon's internal state. Will use the internal mutex.

        Parameters
        ----------
        new_state : State
            The state to tranistion to.

        Returns
        -------
        bool
            True on succesful transistion and False on failure.
        """
        valid_change = True

        if new_state not in self._state_transistions[self._current_state]:
            logging.critical("unknown state: " + str(new_state))
            valid_change = False
        else:
            logging.debug("changing to state " + str(new_state))
            self._lock.acquire()
            self._current_state = new_state
            self._lock.release()

        return valid_change

    def quit(self):
        # stop working thread
        self._running = False
        if self._working_thread.is_alive():
            self._working_thread.join()

    # -------------------------------------------------------------------------
    # dbus properties

    @property
    def CurrentStateValue(self) -> int:
        """
        Getter for the curent state's enum value.

        Returns
        -------
        int
            State's enum value as an it.
        """
        return self._current_state.value

    @property
    def CurrentStateName(self) -> str:
        """
        Getter for the curent state's name.

        Returns
        -------
        str
            State's enum value as a str.
        """
        return self._current_state.name

    @property
    def CurrentInstructionType(self) -> str:
        """
        Getter for the current instruction type.

        Returns
        -------
        str
            Instruction type i.e. install_pkg, remove_pkg, bash_script.
        """
        return self._updater.instruction_type

    @property
    def CurrentInstructionItem(self) -> str:
        """
        Getter for the current instruction item.

        Returns
        -------
        str
            What is being install, remove, or ran.
        """
        return self._updater.instruction_item

    @property
    def CurrentArchiveFile(self) -> str:
        """
        Getter for current archive file.

        Returns
        -------
        str
            The current archive filename.
        """
        return self._updater.archive_file

    @property
    def AvailableArchiveFiles(self) -> int:
        """
        Getter current archvice files available to run.

        Returns
        -------
        int
            The number of archive files in the cache that can be run.
        """
        return self._updater.available_archive_files

    # -------------------------------------------------------------------------
    # dbus methods

    def AddArchiveFile(self, filepath: str) -> bool:
        """
        Adds file to archive file cache.

        Parameters
        ----------
        filepath : str
            Absolute path to archive file to add to cache.

        Returns
        -------
        bool
            True if file was added or False on failure.
        """
        return self._updater.add_archive_file(filepath)

    def Update(self) -> bool:
        """
        Load the oldest archive file in cache and runs update.

        Returns
        -------
        bool
            True if updated worked or False on failure.
        """

        ret = False
        if self._current_state == State.standby:
            ret = self._change_state(State.update)

        return ret

    def MakePackageListFile(self) -> str:
        """
        Make a file with a list of all the files installed and their versions.
        Will use a dbus signal to asynchronously reply.

        Returns
        -------
        bool
            True if package list file is being made or False on failure.
        """

        if self._current_state != State.update:
            self._make_pkg_list = True
            return False

        return True


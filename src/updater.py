#!/usr/bin/env python3


from pathlib import Path
from enum import Enum
import threading, os, sys, re, subprocess, shutil, time, syslog, tarfile
from updater_state_machine import UpdaterStateMachine, State
from updater_apt import UpdaterApt


DBUS_INTERFACE_NAME = "org.OreSat.LinuxUpdater"
CACHE_DIR = '/tmp/oresat-linux-updater/cache/'
WORKING_DIR = '/tmp/oresat-linux-updater/working/'
SLEEP_TIME_S = 1 # seconds, time that sleep and failed state sleeps for


class LinuxUpdater(object):
    dbus = """
    <node>
        <interface name="org.OreSat.LinuxUpdater">
            <method name='AddArchiveFile'>
                <arg type='s' name='file_path' direction='in'/>
                <arg type='b' name='output' direction='out'/>
            </method>
            <method name='StartUpdate'>
                <arg type='b' name='output' direction='out'/>
            </method>
            <method name='ForceUpdate'>
                <arg type='s' name='file_path' direction='in'/>
                <arg type='b' name='output' direction='out'/>
            </method>
            <method name='GetAptListOutput'>
                <arg type='b' name='output' direction='out'/>
            </method>
            <property name="CurrentState" type="d" access="read">
                <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
            </property>
            <property name="CurrentArchiveFile" type="s" access="read">
                <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
            </property>
            <property name="AvailableArchiveFiles" type="d" access="read">
                <annotation name="org.freedesktop.DBus.Property.EmitsChangedSignal" value="true"/>
            </property>
        </interface>
    </node>
    """ # this wont work in __init__()


    # signals
    PropertiesChanged = signal()


    def __init__(self):
        # make directories for updater, if not found
        Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
        Path(WORKING_DIR).mkdir(parents=True, exist_ok=True)

        # state machine set up
        self._state_machine = UpdaterStateMachine(State.SLEEP.value)

        # apt set up
        self._updater_apt = UpdaterApt()

        # archive fields set up
        self._archive_file_name = ""
        self._available_archive_files = len(os.listdir(CACHE_DIR))

        # thread set up
        self.__lock = threading.Lock()
        self.__running = True
        self.__working_thread = threading.Thread(target=self.__working_loop, name="working-thread")
        self.__working_thread.start() # start working thread


    def quit(self):
        """ Use to stop all threads nicely """
        self.__running = False
        if self.__working_thread.is_alive():
            self.__working_thread.join()


    # ------------------------------------------------------------------------
    # dbus properties


    @property
    def CurrentState(self):
        return self._state_machine.current_state


    @property
    def CurrentArchiveFile(self):
        return self._archive_file_name


    @property
    def AvailableArchiveFiles(self):
        return self._available_archive_files


    # ------------------------------------------------------------------------
    # dbus methods


    def AddArchiveFile(self, file_path):
        # (str) -> bool
        """ copies file into CACHE_DIR """
        if(file_path[0] != '/'):
            syslog.syslog(syslog.LOG_ERR, "not an absolute path: " + file_path)
            return False

        # TODO fix this
        """
        # check for valid update file
        if not re.match(r"(update-\d\d\d\d-\d\d-\d\d-\d\d-\d\d\.tar\.gz)", self.__archive_file_path):
            syslog.syslog(syslog.LOG_ERR, "Not a valid update file")
            return
        """

        self.__lock.acquire()
        ret = shutil.copy(file_path, CACHE_DIR)

        if CACHE_DIR in ret:
            self._available_archive_files = len(os.listdir(CACHE_DIR)) # not += 1
            # this will handle file overrides
            self.__lock.release()
            return True

        self.__lock.release()
        return False # failed to copy


    def StartUpdate(self):
        # () -> bool
        """ Start updaing if in sleep state """
        rv = True

        if self._state_machine.current_state == State.SLEEP.value:
            self.__lock.acquire()
            self.__change_state(State.UPDATE.value)
            self.__lock.release()
        else:
            rv = False

        return True


    def GetAptListOutput(self):
        """ To stop updaing """
        # () -> bool
        return True


    # ------------------------------------------------------------------------
    # non-dbus class methods

    def __change_state(self, new_state):
        # (int) -> bool
        """
        Wrapper for updater state machine change state method. If the
        transistion was valid emit the PropertiesChanged signal. All function
        in the updater should call this function not the state machine fucntion
        directly.
        """
        if self._state_machine.change_state(new_state):
            self.PropertiesChanged(INTERFACE_NAME, {"CurrentState": self._state_machine.current_state}, [])
            return True
        return False


    def __working_loop(self):
        # () -> bool
        while(self.__running):
            if self._state_machine.current_state == State.FAILED.value:
                time.sleep(SLEEP_TIME_S)
            elif self._state_machine.current_state == State.SLEEP.value:
                time.sleep(SLEEP_TIME_S)
            elif self._state_machine.current_state == State.PREUPDATE.value:
                self.__pre_update()
            elif self._state_machine.current_state == State.UPDATE.value:
                self.__update()
            elif self._state_machine.current_state == State.REVERT.value:
                self.__revert()
            elif self._state_machine.current_state == State.FORCE.value:
                self.__force()
            else: # should not happen
                syslog.syslog(syslog.LOG_ERR, "current_state is set to an unknowned state.")
                self.__lock.acquire()
                self.__change_state(State.FAILED.value)
                self.__lock.release()


    def __pre_update(self):
        # () -> bool
        """
        Load oldest update file if one exist
        Update thread function.
        Finds the oldest update file and starts update
        """

        archive_file_path = ""

        # see if any update file exist
        list_of_files = os.listdir(CACHE_DIR)
        if not list_of_files:
            self.__lock.acquire()
            self.__change_state(State.SLEEP.value)
            self.__lock.release()
            return True # done, empty, no update files

        self.__lock.acquire()
        self._archive_file_name = list_of_files[0] # get 1st file
        archive_file_path = CACHE_DIR + self._archive_file_name
        self.__lock.release()

        # copy file into working dir
        ret_path = shutil.copy(archive_file_path, WORKING_DIR)
        if CACHE_DIR in ret_path:
            syslog.syslog(syslog.LOG_ERR, "Failed to copy into working dir")
            return False

        # open_archive_file update file
        t = tarfile.open(ret_path, "r:gz")
        if not t:
            syslog.syslog(syslog.LOG_ERR, "Open archive failed")
            return False
        else:
            t.extractall()
            t.close()

        self.__lock.acquire()
        self.__change_state(State.UPDATE.value)
        self.__lock.release()
        return True


    def __update(self):
        # () -> bool
        """
        Load oldest update file if one exist
        Update thread function.
        Finds the oldest update file and starts update
        """

        if not self.__parse_update_file():
            self.__lock.acquire()
            self.__change_state(State.REVERT.value)
            self.__lock.release()
            return False

        self.__lock.acquire()

        # clear working dir and remove update deb pkg
        shutil.rmtree(WORKING_DIR)
        Path(WORKING_DIR).mkdir(parents=True, exist_ok=True)
        os.remove(archive_file_path)
        self._archive_file_name = ""
        self._available_archive_files -= 1
        self.__change_state(State.SLEEP.value)

        self.__lock.release()
        return True


    def __revert(self, err):
        # (str) -> bool
        """
        Update failed reverting all part of update and clearing
        working and update directories.
        """

        # TODO do revert

        self.__lock.acquire()

        # remove all updater files
        shutil.rmtree(WORKING_DIR)
        shutil.rmtree(CACHE_DIR)
        Path(WORKING_DIR).mkdir(parents=True, exist_ok=True)
        Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)

        self._available_archive_files = 0
        self._archive_file_name = ""


        self.__change_state(State.SLEEP.value)
        self.__lock.release()
        return True


    def __force(self):
        # () -> bool
        """
        """

        if not self.__parse_update_file():
            self.__lock.acquire()
            self.__change_state(State.FAILED.value)
            self.__lock.release()
            return False

        self.__lock.acquire()

        # clear working dir and remove update deb pkg
        shutil.rmtree(WORKING_DIR)
        Path(WORKING_DIR).mkdir(parents=True, exist_ok=True)
        os.remove(archive_file_path)
        self._archive_file_name = ""
        self._available_archive_files -= 1
        self.__change_state(State.SLEEP.value)

        self.__lock.release()
        return True


    def __parse_update_file(self):
        # () -> bool
        """
        Install all deb files in WORKING_DIR, remove all packages listed in
        remove.txt, and run all bash script in WORKING_DIR.
        """

        deb_files = []
        remove_pkgs = []

        # install packages
        for file in glob.glob(WORKING_DIR + "*.deb"):
            deb_files.append(file)

        if deb_files.size > 0:
            if not self._updater_apt.remove_packages(deb_files):
                syslog.syslog(syslog.LOG_ERR, "Remove package failed.")
                return False

        # remove packages
        with open(WORKING_DIR + 'remove.txt', 'r') as f:
            pkg = f.readline().strip()
            if not self._updater_apt.install_package(pkg):
                syslog.syslog(syslog.LOG_ERR, "Install package failed.")
                return False

        # run bash scripts
        for file in glob.glob(WORKING_DIR + "*.sh"):
            if subprocess.run(["/bin/bash/ ", file]) != 0:
                syslog.syslog(syslog.LOG_ERR, file + " exited with failure.")
                return False

        return True


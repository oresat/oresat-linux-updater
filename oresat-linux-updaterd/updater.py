from pathlib import Path
import threading, os, sys, re, subprocess, shutil, time, syslog, tarfile
from updater_state_machine import UpdaterStateMachine, State
from updater_apt import UpdaterApt


class LinuxUpdater():

    def _init_(self):
        # make directories for updater, if not found
        Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
        Path(WORKING_DIR).mkdir(parents=True, exist_ok=True)

        # state machine setup
        self._state_machine = UpdaterStateMachine(State.SLEEP.value)

        # apt setup
        self._updater_apt = UpdaterApt()

        # archive fields setup
        self._archive_file_name = ""
        self._available_archive_files = len(os.listdir(CACHE_DIR))

        # thread safe setup
        self._lock = threading.Lock()

        # state flag
        self._running = False


    def run(self):
        self._running = True
        syslog.syslog(syslog.LOG_DEBUG, "OreSat Linux Updater started.")

        while(self._running):
            if self._state_machine.current_state == State.FAILED.value:
                time.sleep(SLEEP_TIME_S)
            elif self._state_machine.current_state == State.SLEEP.value:
                time.sleep(SLEEP_TIME_S)
            elif self._state_machine.current_state == State.PREUPDATE.value:
                self._pre_update()
            elif self._state_machine.current_state == State.UPDATE.value:
                self._update()
            elif self._state_machine.current_state == State.REVERT.value:
                self._revert()
            elif self._state_machine.current_state == State.FORCE.value:
                self._force()
            else: # should not happen
                syslog.syslog(syslog.LOG_CRIT, "current_state is set to an unknowned state.")
                self._lock.acquire()
                self._change_state(State.FAILED.value)
                self._lock.release()



    def stop(self):
        self._running = False
        syslog.syslog(syslog.LOG_DEBUG, "OreSat Linux Updater quit.")


    def add_archive_file(self, file_path):
        # (str) -> bool
        """ copies file into CACHE_DIR """
        if(file_path[0] != '/'):
            syslog.syslog(syslog.LOG_ERR, "not an absolute path: " + file_path)
            return False

        # TODO fix this
        """
        # check for valid update file
        if not re.match(r"(update-\d\d\d\d-\d\d-\d\d-\d\d-\d\d\.tar\.gz)", self._archive_file_path):
            syslog.syslog(syslog.LOG_ERR, "Not a valid update file")
            return
        """

        self._lock.acquire()
        ret = shutil.copy(file_path, CACHE_DIR)

        if CACHE_DIR in ret:
            self._available_archive_files = len(os.listdir(CACHE_DIR)) # not += 1
            # this will handle file overrides
            self._lock.release()
            return True

        self._lock.release()
        return False # failed to copy


    def start_update(self):
        # () -> bool
        """ Start updating if in sleep state """
        rv = True

        if self._state_machine.current_state == State.SLEEP.value:
            self._lock.acquire()
            self._change_state(State.UPDATE.value)
            self._lock.release()
        else:
            rv = False

        return True


    def get_pkg_installed_file(self):
        pass


    def change_state(self, new_state):
        # (int) -> bool
        """
        Wrapper for updater state machine change state method for the dbus
        adaptor to call.
        """

        if self._state_machine.change_state(new_state):
            return True
        return False



    def _pre_update(self):
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
            self._lock.acquire()
            self._change_state(State.SLEEP.value)
            self._lock.release()
            return True # done, empty, no update files

        self._lock.acquire()
        self._archive_file_name = list_of_files[0] # get 1st file
        archive_file_path = CACHE_DIR + self._archive_file_name
        self._lock.release()

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

        self._lock.acquire()
        self._change_state(State.UPDATE.value)
        self._lock.release()
        return True


    def _update(self):
        # () -> bool
        """
        Load oldest update file if one exist
        Update thread function.
        Finds the oldest update file and starts update
        """

        if not self._parse_update_file():
            self._lock.acquire()
            self._change_state(State.REVERT.value)
            self._lock.release()
            return False

        self._lock.acquire()

        # clear working dir and remove update deb pkg
        shutil.rmtree(WORKING_DIR)
        Path(WORKING_DIR).mkdir(parents=True, exist_ok=True)
        os.remove(archive_file_path)
        self._archive_file_name = ""
        self._available_archive_files -= 1
        self._change_state(State.SLEEP.value)

        self._lock.release()
        return True


    def _revert(self, err):
        # (str) -> bool
        """
        Update failed reverting all part of update and clearing
        working and update directories.
        """

        # TODO do revert

        self._lock.acquire()

        # remove all updater files
        shutil.rmtree(WORKING_DIR)
        shutil.rmtree(CACHE_DIR)
        Path(WORKING_DIR).mkdir(parents=True, exist_ok=True)
        Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)

        self._available_archive_files = 0
        self._archive_file_name = ""


        self._change_state(State.SLEEP.value)
        self._lock.release()
        return True


    def _force(self):
        # () -> bool
        """
        """

        if not self._parse_update_file():
            self._lock.acquire()
            self._change_state(State.FAILED.value)
            self._lock.release()
            return False

        self._lock.acquire()

        # clear working dir and remove update deb pkg
        shutil.rmtree(WORKING_DIR)
        Path(WORKING_DIR).mkdir(parents=True, exist_ok=True)
        os.remove(archive_file_path)
        self._archive_file_name = ""
        self._available_archive_files -= 1
        self._change_state(State.SLEEP.value)

        self._lock.release()
        return True


    def _parse_update_file(self):
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


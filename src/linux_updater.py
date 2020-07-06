from pathlib import Path
import threading, os, sys, re, subprocess, shutil, time, syslog, tarfile
from datetime import datetime


class LinuxUpdater():
    """
    The main class for linux updater.
    """

    def __init__(self):
        self._working_dir = "/tmp/oresat-linux-updater/"
        self._file_cache_dir = "/var/cache/oresat-linux-updater"

        # make directory for updater, if not found
        Path(self._working_dir).mkdir(parents=True, exist_ok=True)

        # apt setup
        self._pkg_manager = AptInterface()

        # archive file cache
        self._file_cache = FileCache(self._file_cache_dir)

        # thread safe setup
        self._lock = threading.Lock()

        # state
        self._current_state = ""


    def add_archive_file(self, filepath):
        # type: (str) -> bool
        """
        Copies file into cache directory for later updates.

        Parameters
        ----------
        filename : str
            Filepath to archive file.

        Returns
        -------
        bool
            True if file was added or False on failure.
        """

        if(file_path[0] != '/'):
            syslog.syslog(syslog.LOG_ERR, "Not an absolute path: " + filepath)
            return False

        # check for valid update file
        if not re.match(r"(update-\d\d\d\d-\d\d-\d\d-\d\d-\d\d\.tar\.gz)", filepath):
            syslog.syslog(syslog.LOG_ERR, "Not a valid update filename.")
            return False

        self._lock.acquire()
        self._file_cache.add(filepath)
        self._lock.release()
        return True


    def get_pkg_list_file(self):
        # type: () -> str
        """
        Get a file with a list of pkgs installed.

        Returns
        -------
        str
            The absolute path to file.
        """

        # make a filename for the file
        date_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filepath = "pkg-list-" + date_str + ".txt"

        # make file data
        pkg_list = self._pkg_manager.package_list()
        pkg_list_str = json.dumps(pkg_list)

        # make file
        with open("/tmp/" + filepath, "w") as f:
            f.write(pkg_list_str)

        return filepath


    def current_state(self):
        # type: () -> str
        """
        Get the current state.

        Returns
        -------
        str
            The current state of the updater.
        """

        return self._current_state


    def update(self):
        # type: () -> bool
        """
        Load oldest update file if one exist and runs the update.

        Returns
        -------
        bool
            True if the update worked or False on failure.
        """
        instructions_file = self._working_dir + "instructions.txt"

        # get archive file
        archive_filepath = self._file_cache.get(self._working_dir)
        if not archive_file:
            return True # no file

        # open the archive file
        t = tarfile.open(archive_filepath, "r:gz")
        t.extractall()
        t.close()

        if os.path.isfile(instruction_file):
            return False # no archive file

        instructions_str = ""
        with open(instructions_file,'r') as f:
            instructions_str = f.read()

        instructions = json.load(instructions_str)

        if not self._run_instructions(instructions):
            return False

        return True


    def _run_instructions(self, instructions):
        # type: ([[str]]) -> bool
        """
        Run the instructions to install packages, remove packages, or run
        bash scripts. Will log any faiilures.

        Parameters
        ----------
        instructions : [[str]]
            An array of instruction type str and filenames str. Where
            instruction type can be "install_pkg", "remove_pkg, or
            "bash_script".

        Returns
        -------
        bool
            True if the update worked or False on failure.
        """

        ret = True

        # run instructions
        for i in instructions:
            i_type = i[0]
            i_file = self._working_dir + i[1]

            if type == "install_pkg":
                if not self._pkg_manager.install_pkg(i_file):
                    syslog.syslog(syslog.LOG_ERR, "Install " + i[1] + " package failed.")
                    ret = False
                    break
            elif type == "remove_pkg":
                if not self._pkg_manager.remove_pkg(i_file):
                    syslog.syslog(syslog.LOG_ERR, "Remove " + i[1] + " package failed.")
                    ret = False
                    break
            elif type == "bash_script":
                if subprocess.run(["/bin/bash/ ", i_file]) != 0:
                    syslog.syslog(syslog.LOG_ERR, i_file + " exited with failure.")
                    ret = False
                    break
            else:
                syslog.syslog(syslog.LOG_ERR, "Unkown instruction type: " + i[0] + ".")
                ret = False
                break

        return True


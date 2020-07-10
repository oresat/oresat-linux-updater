from pathlib import Path
import threading, os, sys, re, subprocess, shutil, time, syslog, tarfile
from datetime import datetime


class LinuxUpdater():
    """
    The main class for linux updater.
    """


    def __init__(self, working_dir):
        # type: (str) -> ()
        """
        Parameters
        ----------
        working_dir : str
            Absolute path to a directory for the LinuxUpdater to use.
        """

        # apt setup
        self._pkg_manager = AptInterface()

        self._working_dir = working_dir

        self._archive_file = ""
        self._instruction_type = ""
        self._instruction_item = ""


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


    def update(self):
        # type: () -> bool
        """
        Load oldest update file if one exist and runs the update.

        Returns
        -------
        bool
            True if the update worked or False on failure.
        """

        # move archive file into working dir
        archive_filepath = self._file_cache.get(self._working_dir)
        if not archive_file:
            return True # no file

        return self._update(archive_filepath)


    def _update(self, archive_filepath):
        # type: (str) -> bool
        """
        Runs the update. Archive file should be in working directory.

        Parameters
        ----------
        archive_filepath : str
            Path to archvice file.

        Returns
        -------
        bool
            True if the update worked or False on failure.
        """

        ret = True
        instructions_str = ""
        instructions_file = self._working_dir + "instructions.txt"
        self._archive_file = archive_filepath

        # open the archive file
        t = tarfile.open(archive_filepath, "r:gz")
        t.extractall(path=self._working_dir)
        t.close()

        if os.path.isfile(instruction_file):
            return False # no archive file

        with open(instructions_file,'r') as f:
            instructions_str = f.read()

        instructions = json.load(instructions_str)

        # run instructions
        for i in instructions:
            self._instruction_type = i["type"]
            self._instruction_item = i["item"]

            if i["type"] == "install_pkg":
                if not self._pkg_manager.install(self._working_dir + i["item"]):
                    error_msg = "Install " + i["item"] + " package failed."
                    syslog.syslog(syslog.LOG_ERR, error_msg)
                    ret = False
                    break
            elif i["type"] == "remove_pkg":
                if not self._pkg_manager.remove(self._working_dir + i["item"]):
                    error_msg = "Remove " + i["item"] + " package failed."
                    syslog.syslog(syslog.LOG_ERR, error_msg)
                    ret = False
                    break
            elif i["type"] == "bash_script":
                if subprocess.run(["/bin/bash ", i["item"]]) != 0:
                    error_msg = i["item"] + " exited with failure."
                    syslog.syslog(syslog.LOG_ERR, error_msg)
                    ret = False
                    break
            else:
                error_msg = "Unkown instruction type: " + i_type + "."
                syslog.syslog(syslog.LOG_ERR, error_msg)
                ret = False
                break

        self._instruction_type = ""
        self._instruction_item = ""
        return True


    @property
    def archive_file():
        return self._archive_file


    @property
    def instruction_type():
        return self._instruction_type


    @property
    def item_item():
        return self._instruction_item

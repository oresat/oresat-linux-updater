"""linux updater"""

import os
import tarfile
import json
import logging
import subprocess
from datetime import datetime
from .apt_interface import AptInterface
from .file_cache import FileCache


class LinuxUpdater():
    """
    The main class for linux updater.
    """

    def __init__(self,
                 working_dir: str,
                 cache_dir_path: str
                 ):
        """
        Parameters
        ----------
        working_dir : str
            Path to a directory for the LinuxUpdater to use.
        cache_dir_path: str
            Path to a directory for the LinuxUpdater to cache packages.
        """

        self._pkg_manager = AptInterface()
        self._file_cache = FileCache(cache_dir_path)
        self._working_dir = working_dir

        # informative attributes when updating
        self._archive_file = ""
        self._instruction_type = ""
        self._instruction_item = ""

    def get_pkg_list_file(self) -> str:
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

    def update(self) -> bool:
        """
        Load oldest update file if one exist and runs the update.

        Returns
        -------
        bool
            True if the update worked or False on failure.
        """

        # move archive file into working dir
        archive_filepath = self._file_cache.get(self._working_dir)
        if not archive_filepath:
            return True  # no file

        return self._update(archive_filepath)

    def _update(self, archive_filepath: str) -> bool:
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
        with tarfile.open(archive_filepath, "r:gz") as tfile:
            tfile.extractall(path=self._working_dir)

        if os.path.isfile(instructions_file):
            return False  # no archive file

        with open(instructions_file, 'r') as f:
            instructions_str = f.read()

        instructions = json.load(instructions_str)

        # run instructions
        for i in instructions:
            self._instruction_type = i["type"]
            self._instruction_item = i["item"]
            i_item_path = self._working_dir + i["item"]

            if i["type"] == "install_pkg":
                if not self._pkg_manager.install(i_item_path):
                    error_msg = "Install " + i["item"] + " package failed."
                    logging.error(error_msg)
                    ret = False
                    break
            elif i["type"] == "remove_pkg":
                if not self._pkg_manager.remove(i_item_path):
                    error_msg = "Remove " + i["item"] + " package failed."
                    logging.error(error_msg)
                    ret = False
                    break
            elif i["type"] == "bash_script":
                if subprocess.run(["/bin/bash ", i["item"]], check=True) != 0:
                    error_msg = i["item"] + " exited with failure."
                    logging.error(error_msg)
                    ret = False
                    break
            else:
                error_msg = "Unkown instruction type: " + i["type"] + "."
                logging.error(error_msg)
                ret = False
                break

        self._instruction_type = ""
        self._instruction_item = ""
        return ret

    @property
    def archive_file(self):
        """The current archive file being used."""
        return self._archive_file

    @property
    def instruction_type(self):
        """
        The current instuction type. i.e.: install_pkg, remove_pkg, bash_script
        """
        return self._instruction_type

    @property
    def item_item(self):
        """
        The current instuction item. i,e,:
        - the *.deb file being install
        - the name of the package being removed
        - the name of the bashscrip being run
        """
        return self._instruction_item

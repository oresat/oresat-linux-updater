"""linux updater"""

import os
import re
import tarfile
import logging
import json
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from oresat_updaterd.apt_interface import AptInterface
from oresat_updaterd.file_cache import FileCache

_ARCHIVE_FILE_REGEX = r".*_update_\d\d\d\d_\d*_\d*_\d*_\d*_\d*.tar.gz"


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

        logging.debug("working dir is %s", working_dir)
        logging.debug("file cache dir is %s", cache_dir_path)

        logging.debug("setup up apt cache")
        self._pkg_manager = AptInterface()
        logging.debug("setup up archive file cache")
        self._file_cache = FileCache(cache_dir_path)
        self._working_dir = working_dir

        # If the directory does not make it
        Path(working_dir).mkdir(parents=True, exist_ok=True)

        # informative attributes when updating
        self._instruction_type = ""
        self._instruction_item = ""
        self._archive_file = ""

    def get_pkg_list_file(self) -> str:
        """
        Get a file with a list of pkgs installed.

        Returns
        -------
        str
            The absolute path to tar file with the pkg list.
        """

        # make a filename for the file
        date_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        myhost = os.uname()[1]
        txt_filename = myhost + "_pkg-list_" + date_str + ".txt"
        txt_file = "/tmp/" + txt_filename
        tar_file = "/tmp/" + myhost + "_pkg-list_" + date_str + ".tar.gz"

        # get pkg list as a json str
        pkg_json = self._pkg_manager.package_list()

        # make txt file
        with open(txt_file, "w") as fptr:
            fptr.write(pkg_json)

        # make tar
        with tarfile.open(tar_file, "w:gz") as fptr:
            fptr.add(txt_file, arcname=txt_filename)

        os.remove(txt_file)

        logging.debug("%s was made", tar_file)

        return tar_file

    def add_archive_file(self, filepath: str) -> bool:
        """
        Load oldest update file if one exist and runs the update.
        """

        try:
            self._file_cache.add(filepath)
            logging.info("%s was added to cache", filepath)
        except:
            logging.error("failed to add %s to cache", filepath)
            return False
        return True

    def update(self) -> bool:
        """
        Load oldest update file if one exist and runs the update.

        Returns
        -------
        bool
            True if the update worked or False on failure.
        """

        resume = False
        wd_files = os.listdir(self._working_dir)

        if wd_files:
            logging.info("Files found in working directory, trying to resume")

            for f in wd_files:
                if re.search(_ARCHIVE_FILE_REGEX, f):  # check for tar
                    logging.info("%s found", f)
                    self._archive_file = f

                    if f == "instructions.txt":  # check for instructions.txt
                        logging.info("instructions.txt found, skipping untar")
                    else:
                        # open the archive file
                        logging.debug("untar %s", f)
                        with tarfile.open(f, "r:gz") as tfile:
                            tfile.extractall(path=self._working_dir)

                    resume = True
                    break

            if not resume:  # clear dir
                logging.error("Can't resume update, cleaning working dir")
                self._archive_file = ""

                # clean up working dir
                shutil.rmtree(self._working_dir)
                Path(self._working_dir).mkdir(parents=True, exist_ok=True)

        if not resume:  # get new archive file from cache
            archive_filepath = self._file_cache.get(self._working_dir)

            if not archive_filepath:
                logging.info("No files in cache")
                return True  # no file, nothing to do

            self._archive_file = os.path.basename(archive_filepath)
            logging.debug("Starting update with %s", archive_filepath)

            # open the archive file
            with tarfile.open(archive_filepath, "r:gz") as tfile:
                logging.debug("untar %s", archive_filepath)
                tfile.extractall(path=self._working_dir)

        return self._update()

    def _update(self) -> bool:
        """
        Runs the update. Archive file should be in working directory.

        Returns
        -------
        bool
            True if the update worked or False on failure.
        """

        ret = True
        instructions_str = ""
        instructions_file = self._working_dir + "instructions.txt"

        if not os.path.isfile(instructions_file):
            logging.error("%s not found", instructions_file)
            return False  # no archive file

        with open(instructions_file, 'r') as fptr:
            instructions_str = fptr.read()

        instructions = json.loads(instructions_str)

        # run instructions
        for i in instructions:
            i_type = i["type"]
            i_item = i["item"]
            self._instruction_type = i_type
            self._instruction_item = i_item

            msg = i_type + " " + i_item
            logging.debug(msg)

            if i_type == "install_pkg":
                if not self._pkg_manager.install(self._working_dir + i_item):
                    logging.error("Install %s package failed.", i_item)
                    ret = False
                    break
            elif i_type == "remove_pkg":
                if not self._pkg_manager.remove(i_item):
                    logging.error("Remove %s package failed.", i_item)
                    ret = False
                    break
            elif i_type == "bash_script":
                command = "bash " + self._working_dir + i_item
                logging.debug("running %s", command)
                if subprocess.call(command, shell=True) != 0:
                    logging.error("%s exited with failure.", i_item)
                    ret = False
                    break
            else:
                logging.error("Unkown instruction type: %s", i_type)
                ret = False
                break

        if ret:
            # clean workng directory
            shutil.rmtree(self._working_dir)
            Path(self._working_dir).mkdir(parents=True, exist_ok=True)
            self._file_cache.remove(self._archive_file)

        self._instruction_type = ""
        self._instruction_item = ""
        self._archive_file = ""
        return ret

    @property
    def archive_file(self):
        """The current archive file being used."""
        return self._archive_file

    @property
    def available_archive_files(self):
        """The number of archive files in cache"""
        return len(self._file_cache)

    @property
    def instruction_type(self):
        """
        The current instuction type. i.e.: install_pkg, remove_pkg, bash_script
        """
        return self._instruction_type

    @property
    def instruction_item(self):
        """
        The current instuction item. i,e,:
        - the *.deb file being install
        - the name of the package being removed
        - the name of the bashscrip being run
        """
        return self._instruction_item
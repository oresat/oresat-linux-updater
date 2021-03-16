"""Make update files for OreSat Linux Updater daemon."""

import sys
from os import listdir, remove, walk, stat
from os.path import isfile, basename
from shutil import copyfile
from pathlib import Path
from oresat_linux_updater.olm_file import OLMFile
from oresat_linux_updater.instruction import Instruction, InstructionType
from oresat_linux_updater.update_archive import create_update_archive
from oresat_linux_updater.status_archive import read_dpkg_status_file
from apt.cache import Cache


OLU_DIR = str(Path.home()) + "/.oresat_linux_updater/"
ROOT_DIR = OLU_DIR + "root/"
DOWNLOAD_DIR = ROOT_DIR + "var/cache/apt/archives/"
DPKG_STATUS_FILE = ROOT_DIR + "var/lib/dpkg/status"
UPDATE_CACHE_DIR = OLU_DIR + "update_cache/"
STATUS_CACHE_DIR = OLU_DIR + "status_cache/"
SYSTEM_APT_SOURCES_FILE = "/etc/apt/sources.list"
SYSTEM_SIGNATURES_DIR = "/var/lib/apt/lists/"
OLU_APT_SOURCES_FILE = ROOT_DIR + "etc/apt/sources.list"
OLU_SIGNATURES_DIR = ROOT_DIR + "var/lib/apt/lists/"


class UpdateMaker():
    """A class for making updates for OreSat Linux Updater daemon"""

    def __init__(self, board: str):
        """
        Parameters
        ----------
        board: str
            The board to make the update for.
        """
        self._board = board
        self._status_file = ""
        self._board = board
        self._cache = Cache(rootdir=ROOT_DIR)
        self._deb_pkgs = []
        self._inst_list = []

        print("updating cache")
        self._cache.update(raise_on_error=False)
        self._cache.open()

        # copying the context of the real root apt source.list file into the local one
        if stat(OLU_APT_SOURCES_FILE).st_size == 0 or not isfile(OLU_APT_SOURCES_FILE):
            copyfile(SYSTEM_APT_SOURCES_FILE, OLU_APT_SOURCES_FILE)    
        
            # adding OreSat Debian apt repo
            with open(OLU_APT_SOURCES_FILE, 'a') as f:
                f.write('deb [trusted=yes] https://debian.oresat.org/packages ./') 

        # copying the apt repo signatures
        if len(listdir(OLU_SIGNATURES_DIR)) == 3:
            for root, dirs, files in walk(SYSTEM_SIGNATURES_DIR): 
                for file in files:
                    if file != 'lock':
                        copyfile(SYSTEM_SIGNATURES_DIR + file, OLU_SIGNATURES_DIR + file)         

        # clear download dir
        for i in listdir(DOWNLOAD_DIR):
            if i.endswith(".deb"):
                remove(DOWNLOAD_DIR + i)        

        status_files = []
        for i in listdir(STATUS_CACHE_DIR):
            status_files.append(OLMFile(load=i))
        status_files.sort()

        # find latest olu status tar file
        for i in status_files:
            if i.board == board:
                self._status_file = STATUS_CACHE_DIR + i.name
                break

        if self._status_file == "":
            msg = "No status file for {} board in cache".format(board)
            raise FileNotFoundError(msg)

        # update status file
        dpkg_data = read_dpkg_status_file(self._status_file)
        with open(DPKG_STATUS_FILE, "w") as fptr:
            fptr.write(dpkg_data)

        # TODO deal with update files that are not installed yet.

    def add_packages(self, packages: list):
        """Add deb packages to be installed.

        Parameters
        ----------
        packages: list
            A list of deb packages to install on the board.
        """

        if packages == []:
            raise ValueError("Requires a list of packages to install")

        inst_deb_pkgs = []

        for pkg in packages:
            pkg_obj = self._cache[pkg]
            pkg_obj.mark_install()  # this will mark all dependencies too

            # find new packages (dependencies) that are marked
            for deb_pkg in self._cache:
                if deb_pkg.marked_install and \
                        deb_pkg.name not in self._deb_pkgs:
                    self._deb_pkgs.append(deb_pkg.name)
                    inst_deb_pkgs.append(deb_pkg.name)

        new_inst = Instruction(InstructionType.DPKG_INSTALL, inst_deb_pkgs)
        self._inst_list.append(new_inst)

    def remove_packages(self, packages: list):
        """Remove deb packages on board.

        Parameters
        ----------
        packages: list
            A list of deb packages to remove on the board.
        """

        if packages == []:
            raise ValueError("Requires a list of packages to remove")

        new_inst = Instruction(InstructionType.DPKG_REMOVE, packages)
        self._inst_list.append(new_inst)

    def purge_packages(self, packages: list):
        """Purge deb packages on board.

        Parameters
        ----------
        packages: list
            A list of deb packages to remove on the board.
        """

        if packages == []:
            raise ValueError("Requires a list of packages to remove")

        new_inst = Instruction(InstructionType.DPKG_PURGE, packages)
        self._inst_list.append(new_inst)

    def add_bash_scripts(self, bash_scipts: list):
        """Run bash scripts on the board.

        Parameters
        ----------
        bash_scipts: list
            A list of bash script to run on the board.
        """

        if bash_scipts == []:
            raise ValueError("Requires a list of bash scipts to run")

        new_inst = Instruction(InstructionType.BASH_SCRIPT, bash_scipts)
        self._inst_list.append(new_inst)

    def add_support_files(self, support_files: list):
        """Add a support files to update archive.

        Parameters
        ----------
        support_files: list
            A list of support files to add to the update.
        """

        for s_file in support_files:
            if isfile(s_file):
                raise ValueError(" {} was not found".format(s_file))

        new_inst = Instruction(InstructionType.SUPPORT_FILE, support_files)
        self._inst_list.append(new_inst)

    def status(self):
        """Print the contexts of instructions list"""

        for i in self._inst_list:
            print(i)

    def make_update_archive(self):
        """Make the update archive"""

        # download deb files
        self._cache.fetch_archives()

        # replace package name with deb filepath in instruction obj
        for inst in self._inst_list:
            if not inst.type == InstructionType.DPKG_INSTALL:
                continue

            for i in range(len(inst.items)):
                found = False
                for deb_file in listdir(DOWNLOAD_DIR):
                    if not deb_file.endswith(".deb"):
                        continue

                    if deb_file.startswith(inst.items[i]+"_"):
                        inst.items[i] = DOWNLOAD_DIR + deb_file
                        found = True
                        break

                if found is False:
                    break

        print("Making tar")

        update_file = create_update_archive(self._board, self._inst_list, "./")

        print("{} was made".format(update_file))

        # option to move generate updates to the update cache
        command = input("-> Save copy to update cache [Y/n]: ")

        if command == "Y" or command == "y" or command == "yes":
            try:
                copyfile(update_file, UPDATE_CACHE_DIR + basename(update_file))
            except:
                print("An error occurred saving the copy to update cache")
            else:
                print("{} was added to update cache".format(update_file))

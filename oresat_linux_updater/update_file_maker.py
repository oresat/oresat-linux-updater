#!/usr/bin/env python3
"""CLI for making update package for the OreSat Linux updater"""

import os
import sys
import tarfile
from datetime import datetime
from oresat_linux_updater import INST_FILE
from oresat_linux_updater.instructions_list import InstructionsList, \
        InstructionType, Instruction
from apt.cache import Cache

ROOT_DIR = "/home/oresat/root/"
DOWNLOAD_DIR = ROOT_DIR + "var/cache/apt/archives/"


class UpdateCommand(Exception):
    """Invalid commands format"""


class UpdateFileMaker():

    def __init__(self, board: str, filename=""):
        self._board = board
        self._cache = Cache(rootdir="./root/")
        self._cache.update(raise_on_error=False)
        self._cache.open()

        for i in os.listdir(DOWNLOAD_DIR):
            if i.endswith(".deb"):
                os.remove(DOWNLOAD_DIR + i)

        if filename == "":
            self._inst_list = InstructionsList()
        else:
            self._inst_list = InstructionsList(filename)

    def add_packages(self, packages: list):
        """Add deb packages"""

        if packages == []:
            raise UpdateCommand("Requires a list of packages to install")

        for pkg in packages:
            pkg_obj = self._cache[pkg]
            pkg_obj.mark_install()

            pkgs = []

            for pkg in self._cache:
                if pkg.marked_install and \
                        not self._inst_list.has_item(pkg.name):
                    pkgs.append(pkg.name)

        new_inst = Instruction(InstructionType.DPKG_INSTALL, pkgs)
        self._inst_list.append(new_inst)

    def remove_packages(self, packages: list):
        """Remove deb packages"""

        if packages == []:
            raise UpdateCommand("Requires a list of packages to remove")

        new_inst = Instruction(InstructionType.DPKG_REMOVE, packages)
        self._inst_list.append(new_inst)

    def add_bash_scripts(self, bash_scipts: list):
        """Add a bash scipt"""

        if bash_scipts == []:
            raise UpdateCommand("Requires a list of bash scipts to run")

        new_inst = Instruction(InstructionType.BASH_SCRIPT, bash_scipts)
        self._inst_list.append(new_inst)

    def add_support_files(self, support_files: list):
        """Add a support files"""

        for s_file in support_files:
            if os.path.isfile(s_file):
                raise UpdateCommand("File {} was not found".format(s_file))

        new_inst = Instruction(InstructionType.SUPPORT_FILE, support_files)
        self._inst_list.append(new_inst)

    def status(self):
        """Print the contexts of instructions list"""

        for i in self._inst_list:
            print(i)

    def make_update(self):
        """Make the update tar.xz file"""

        date_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        filename = self._board + "_update_" + date_str + ".tar.xz"

        # download deb files
        self._cache.fetch_archives()

        # replace package name with deb filename in instructions obj
        for db in os.listdir(DOWNLOAD_DIR):
            if db.endswith(".deb"):
                for inst in self._inst_list:
                    if inst.type == InstructionType.DPKG_INSTALL:
                        for i in range(len(inst.items)):
                            if db.startswith(inst.items[i]+"_"):
                                inst.items[i] = db
                                break

        with open(INST_FILE, "w") as fptr:
            fptr.write(self._inst_list.json_str)

        print("making tar")

        with tarfile.open(filename, "w:xz") as tar:
            tar.add(INST_FILE)

            for dpkg_file in \
                    self._inst_list.files_needed(InstructionType.DPKG_INSTALL):
                if dpkg_file.endswith(".deb"):
                    tar.add(DOWNLOAD_DIR + dpkg_file, arcname=dpkg_file)

            for bash_script in \
                    self._inst_list.files_needed(InstructionType.BASH_SCRIPT):
                tar.add(bash_script, arcname=os.path.basename(bash_script))

            for support_file in \
                    self._inst_list.files_needed(InstructionType.SUPPORT_FILE):
                tar.add(support_file, arcname=os.path.basename(support_file))

        os.remove(INST_FILE)

        print("{} was made".format(filename))


def usage():
    print("""
    python3 make_update_pacakge.py <board>

    cli commands:
        add-pkg:    add deb package(s)
        remove-pkg: remove deb package(s)
        add-bash:   add bash script(s)
        add-files:  add support file(s)
        status:     print status
        make:       make the update archive file and quit
        quit:       quit the cli
    """)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    maker = UpdateFileMaker(sys.argv[1])

    while True:
        command = input("-> ").split(" ")

        try:
            if command[0] == "status":
                maker.status()
            elif command[0] == "help":
                usage()
            elif command[0] == "add-pkg":
                maker.add_packages(command[1:])
            elif command[0] == "remove-pkg":
                maker.remove_packages(command[1:])
            elif command[0] == "add-bash":
                maker.add_bash_scripts(command[1:])
            elif command[0] == "add-files":
                maker.add_support_files(command[1:])
            elif command[0] == "make":
                maker.make_update()
                break
            elif command[0] == "quit":
                break
            else:
                print("not valid command")
        except Exception as exc:
            print(exc)

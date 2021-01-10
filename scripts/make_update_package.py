#!/usr/bin/env python3
"""CLI for making update package for the OreSat Linux updater"""

import os
import sys
import json
import tarfile
import shutil
from datetime import datetime
from enum import Enum
from collections import OrderedDict
from apt import cache, debfile

BUILD_DIR = "build/"


class InstructionType(Enum):
    install_pkg = 0
    remove_pkg = 1
    bash_script = 2

class UpdateArchiveMaker():

    def __init__(self, pkg_list_file: str):
        self.apt_cache = cache.Cache()
        self.pkg_list = {}
        self.instructions = OrderedDict()

        with open(pkg_list_file) as fptr:
           self.pkg_list = json.load(fptr)


    def is_installed(self, package: str) -> bool:
        if package in self.pkg_list or package in self.instructions:
            return True
        return False

    def add_package(self, package: str) -> bool:
        if not self.is_installed(package):
            self.get_dependencies(package)
            self.instructions[package] = InstructionType.install_pkg

        return True

    def get_dependencies(self, package: str, recs = []) -> bool:

        if self.is_installed(package) or package in recs:
            return True

        recs.append(package)

        # virtual package
        if self.apt_cache.is_virtual_package(package):
            pkg_list = self.apt_cache.get_providing_packages(package)
            for pkg in pkg_list: # find package for virtual package
                if not self.is_installed(pkg.shortname):
                    self.get_dependencies(pkg.shortname, recs)
                    self.instructions[pkg.shortname] = InstructionType.install_pkg

            recs.remove(package)
            return True

        # need to add, find in cache
        try:
            pkg = self.apt_cache[package]
        except KeyError:
            print("{} not found in apt cache".format(package))
            recs.remove(package)
            return False

        # get all dependencies, resurse if needed
        if pkg.shortname == package:
            for dep in pkg.versions[0].dependencies:
                name = dep[0].name

                # deal with ":any" packages
                if name[-4:] == ":any":
                    name = name[:-4]

                if not self.is_installed(name):
                    self.get_dependencies(name, recs)
                    if not self.apt_cache.is_virtual_package(name):
                        self.instructions[name] = InstructionType.install_pkg
        
        recs.remove(package)
        return True

    def status(self):
        for i in self.instructions:
            print("{}: {}".format(i, self.instructions[i].name))

    def make_instruction_txt(self) -> bool:
        data = []
        date_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        myhost = os.uname()[1]
        filename = myhost + "_pkg-list_" + date_str + ".tar.gz"

        os.mkdir(BUILD_DIR)

        for i in self.instructions:
            # add to instructions.txt
            data.append({"type": self.instructions[i].name, "item": i})

            # download package
            pkg_ver = self.apt_cache[i].versions
            for pv in pkg_ver:
                if pv.architecture in ["all", "armhf"]:
                    pv.fetch_binary(BUILD_DIR)
                    break

        with open(BUILD_DIR + "instructions.txt", "w") as fptr:
            json.dump(data, fptr)

        with tarfile.open(filename,"w:gz") as tar:
            for i in os.listdir(BUILD_DIR):
                tar.add(BUILD_DIR + i, arcname=i)

        shutil.rmtree(BUILD_DIR, ignore_errors=True)

        return True


def usage():
    print("""
    python3 make_update_pacakge.py <file>

    cli commands:
        exit:       exit the cli
        add:        add package or bash script
        remove:     remove package
        status:     print status
        make:       make the update archive
    """)


if __name__ == "__main__":
    # remove old build if it still exist
    shutil.rmtree(BUILD_DIR, ignore_errors=True)

    uam = UpdateArchiveMaker(sys.argv[1])
    
    while True:
        command = input("-> ").split(" ")

        if command[0] == "quit":
            break
        elif command[0] == "status":
            uam.status()
        elif command[0] == "make":
            uam.make_instruction_txt()
        elif command[0] == "help":
            usage()
        elif len(command) == 2: # every command below needs argument
            if command[0] == "add":
                uam.add_package(command[1])
                #for pkg in uam.package_dependencies(command[1]):
                #    print(pkg)
            elif command[0] == "remove":
                print("remove")
        else:
            print("not valid command")

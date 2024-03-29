#!/usr/bin/env python3
"""A script for starting a update with a local update archive"""

import os
import sys
import argparse
from pydbus import SystemBus

ISENDER = "org.OreSat.Updater"
IFACE = "org.OreSat.Updater"
OBJECT = "/org/OreSat/Updater"


def properties_changed_cb(*args):
    print("PropertiesChanged returned: ", args[4][0])
    sys.exit(0)


def update_result_cb(*args):
    print("UpdateResult returned: ", args[4][0])
    sys.exit(0)


def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--add", dest="file",
                        help="path to file to install")
    parser.add_argument("-u", "--update", action="store_true",
                        help="start update")
    parser.add_argument("-s", "--status-archive", action="store_true",
                        help="make status archive file")
    parser.add_argument("-l", "--list-updates", action="store_true",
                        help="list update files in cache")
    args = parser.parse_args()

    # set up bus connection
    bus = SystemBus()
    updater = bus.get(IFACE)

    if args.file:
        ret = updater.AddUpdateArchive(os.path.abspath(args.file))
        print("AddUpdateArchive returned: " + str(ret))
    elif args.update:
        ret = updater.Update()
        print("Update returned: " + str(ret))
    elif args.status_archive:
        ret = updater.MakeStatusArchive()
        print("MakeStatusArchive returned: " + ret)
    elif args.list_updates:
        ret = updater.ListUpdates
        print("ListUpdates returned: " + ret)


main()

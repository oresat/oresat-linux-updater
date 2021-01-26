#!/usr/bin/env python3
"""A script for starting a update with a local update archive"""

import os
import argparse
from pydbus import SystemBus
from gi.repository import GLib

ISENDER = "org.oresat.updater"
IFACE = "org.oresat.updater"
OBJECT = "/org/oresat/updater"

parser = argparse.ArgumentParser()

parser.add_argument("-a", "--add", dest="file", help="path to file to install")
parser.add_argument("-u", "--update", action="store_true", help="start update")
parser.add_argument("-s", "--status-file", action="store_true",
                    help="make status tar file")
args = parser.parse_args()


def properties_changed_cb(*args):
    print("PropertiesChanged returned: ", args[4][0])
    exit(0)


def status_file_cb(*args):
    print("StatusFile returned: ", args[4][0])
    exit(0)


def update_result_cb(*args):
    print("UpdateResult returned: ", args[4][0])
    exit(0)


bus = SystemBus()

bus.subscribe(
        sender=ISENDER,
        iface=IFACE,
        signal="PropertiesChanged",
        signal_fired=properties_changed_cb,
        object=OBJECT)

bus.subscribe(
        sender=ISENDER,
        iface=IFACE,
        signal="UpdateResult",
        signal_fired=update_result_cb,
        object=OBJECT)

bus.subscribe(
        sender=ISENDER,
        iface=IFACE,
        signal="StatusFile",
        signal_fired=status_file_cb,
        object=OBJECT)


updater = bus.get(IFACE)

if args.file:
    ret = updater.AddArchiveFile(os.path.abspath(args.file))
    print("AddArchiveFile returned: " + str(ret))
elif args.update:
    ret = updater.Update()
    print("Update returned: " + str(ret))
elif args.status_file:
    ret = updater.MakeStatusFile()
    print("MakeStatusFile returned: " + str(ret))

if not args.file:
    loop = GLib.MainLoop()

    try:
        loop.run()
    except KeyboardInterrupt:
        loop.quit()

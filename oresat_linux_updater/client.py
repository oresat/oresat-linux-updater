#!/usr/bin/env python3
"""A script for starting a update with a local update archive"""

import os
import sys
import argparse
from pydbus import SystemBus
from gi.repository import GLib

ISENDER = "org.oresat.updater"
IFACE = "org.oresat.updater"
OBJECT = "/org/oresat/updater"


def properties_changed_cb(*args):
    print("PropertiesChanged returned: ", args[4][0])
    sys.exit(0)


def status_archive_cb(*args):
    print("StatusArchive returned: ", args[4][0])
    sys.exit(0)


def update_result_cb(*args):
    print("UpdateResult returned: ", args[4][0])
    sys.exit(0)


# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-a", "--add", dest="file",
                    help="path to file to install")
parser.add_argument("-u", "--update", action="store_true",
                    help="start update")
parser.add_argument("-s", "--status-archive", action="store_true",
                    help="make status archive file")
parser.add_argument("-i", "--status-info", action="store_true",
                    help="print status info")
args = parser.parse_args()

# set up bus connection
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
        signal="StatusArchive",
        signal_fired=status_archive_cb,
        object=OBJECT)

updater = bus.get(IFACE)

if args.file:
    ret = updater.AddUpdateArchive(os.path.abspath(args.file))
    print("AddUpdateArchive returned: " + str(ret))
elif args.update:
    ret = updater.Update()
    print("Update returned: " + str(ret))
elif args.status_archive:
    ret = updater.MakeStatusArchive()
    print("MakeStatusArchive returned: " + str(ret))
elif args.status_info:
    print("Status: {} aka {}".format(updater.StatusName, updater.StatusValue))
    print("UpdateArchive: {}".format(updater.UpdateArchive))
    print("AvailableUpdateArchives: {}".format(updater.AvailableUpdateArchives))

if not args.status_archive:
    loop = GLib.MainLoop()

    try:
        loop.run()
    except KeyboardInterrupt:
        loop.quit()

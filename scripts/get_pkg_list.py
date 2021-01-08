#!/usr/bin/env python3
"""Gets the list of all packages install from OreSat Linux updater"""

from os.path import basename
from shutil import move
from pydbus import SystemBus
from gi.repository import GLib

bus = SystemBus()  # connect to bus
updater = bus.get("org.oresat.updater")
loop = GLib.MainLoop()


def package_list_cb(*args):
    """Callback on emitting signal from server"""
    filepath = args[4][0]
    filename = basename(filepath)
    move(filepath, "./" + filename)
    print(filename)
    loop.quit()


# call dbus method
updater.MakePackageListFile()

bus.subscribe(
        sender="org.oresat.updater",
        iface="org.oresat.updater",
        signal="PackageListFile",
        signal_fired=package_list_cb,
        object="/org/oresat/updater")

try:
    loop.run()
except KeyboardInterrupt:
    loop.quit()

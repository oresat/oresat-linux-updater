import sys, os
from pydbus import SystemBus
from gi.repository import GLib
from .linux_updater import LinuxUpdater
from .daemon import Daemon


if __name__ == "__main__":
    daemon_flag = False

    opts, args = getopt.getopt(sys.argv[1:], "dh")
    for opt, arg in opts:
        if opt == "d":
            daemon_flag = True
        elif opt == "h":
            usage()
            exit(0)

    if daemon_flag:
        daemon = Daemon("/run/oresat-linux-updater.pid")
        daemon.run()

    # make updater
    updater_daemon = LinuxUpdaterDaemon()

    # set up dbus wrapper
    bus = SystemBus()
    bus.publish(DBUS_INTERFACE_NAME, updater_daemon)

    # start dbus wrapper
    loop = GLib.MainLoop()

    try:
        loop.run()
    except KeyboardInterrupt as e:
        loop.quit()

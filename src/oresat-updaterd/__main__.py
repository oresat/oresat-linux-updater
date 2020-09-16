"""Main for the linux updater"""

import sys
import os
import getopt
import logging
from pydbus import SystemBus
from gi.repository import GLib
from .linux_updater_daemon import LinuxUpdaterDaemon

DBUS_INTERFACE_NAME = "temp"
APP_NAME = "oresat-updaterd"


def daemonize(pid_file: str):
    """Daemonize the process

    Attributes
    ----------
    PID_FILE: str
        The path to the pid file for the daemon.
    """

    # Check for a pidfile to see if the daemon is already running
    try:
        with open(pid_file, 'r') as pf:
            pid = int(pf.read().strip())
    except IOError:
        pid = None

    if pid:
        sys.stderr.write("pid file {0} already exist.\n".format(PID_FILE))
        sys.exit(1)

    try:
        pid = os.fork()
        if pid > 0:
            # exit from parent
            sys.exit(0)
    except OSError as err:
        sys.stderr.write('fork failed: {0}\n'.format(err))
        sys.exit(1)

    # decouple from parent environment
    os.chdir('/')
    os.setsid()
    os.umask(0)

    # redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    si = open(os.devnull, 'r')
    so = open(os.devnull, 'a+')
    se = open(os.devnull, 'a+')

    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

    pid = str(os.getpid())
    with open(PID_FILE, 'w+') as f:
        f.write(pid + '\n')


def usage():
    """Arg message"""
    message = """"
        usage:\n
        python3 ultra.py      : to run as a process.
        python3 ultra.py -d   : to run as a daemon.
        python3 ultra.py -h   : this message.
        """
    print(message)


if __name__ == "__main__":
    PID_FILE = "/run/oresat-updaterd.pid"
    DAEMON_FLAG = False
    VERBOSE = False

    opts = getopt.getopt(sys.argv[1:], "dvh")
    for opt in opts:
        if opt == "d":
            DAEMON_FLAG = True
        if opt == "v":
            VERBOSE = True
        elif opt == "h":
            usage()
            sys.exit(0)

    if DAEMON_FLAG:
        daemonize(PID_FILE)
        LOG_FILE = "/var/log/" + APP_NAME + ".log"
        WORKING_DIR = "/tmp/" + APP_NAME + "/"
        FILE_CACHE_DIR = "/var/cache/" + APP_NAME + "/"
    else:
        LOG_FILE = APP_NAME + ".log"
        WORKING_DIR = "/tmp/" + APP_NAME + "/"
        FILE_CACHE_DIR = APP_NAME + "/cache/"

        # also send all log message to stderr
        logging.getLogger().addHandler(logging.StreamHandler())

    # turn on logging for debug messages
    if VERBOSE:
        logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG)
    else:
        logging.basicConfig(filename=LOG_FILE, level=logging.INFO)

    # make updater
    updater_daemon = LinuxUpdaterDaemon(
        WORKING_DIR,
        FILE_CACHE_DIR
        )

    # set up dbus wrapper
    bus = SystemBus()
    bus.publish(DBUS_INTERFACE_NAME, updater_daemon)

    # start dbus wrapper
    loop = GLib.MainLoop()

    try:
        loop.run()
    except KeyboardInterrupt:
        loop.quit()

    if DAEMON_FLAG is True:
        os.remove(PID_FILE)  # clean up daemon

"""Main for the linux updater"""

import sys
import os
import getopt
import logging
from pydbus import SystemBus
from gi.repository import GLib
from oresat_linux_updater import FILE_CACHE_DIR
from oresat_linux_updater import LOG_FORMAT
from oresat_linux_updater import LOG_FILE
from oresat_linux_updater import PID_FILE
from oresat_linux_updater import WORKING_DIR
from oresat_linux_updater.linux_updater_daemon import LinuxUpdaterDaemon
from oresat_linux_updater.linux_updater_daemon import DBUS_INTERFACE_NAME


def daemonize(pid_file: str):
    """Daemonize the process

    Attributes
    ----------
    PID_FILE: str
        The path to the pid file for the daemon.
    """

    # Check for a pidfile to see if the daemon is already running
    try:
        with open(pid_file, 'r') as fptr:
            pid = int(fptr.read().strip())
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
    with open(PID_FILE, 'w+') as fptr:
        fptr.write(pid + '\n')


def usage():
    """Arg message"""
    message = """
        usage:\n
        python3 ultra.py      : to run as a process.
        python3 ultra.py -d   : to run as a daemon.
        python3 ultra.py -h   : this message.
        """
    print(message)


def main():
    DAEMON_FLAG = False
    VERBOSE = False

    opts, args = getopt.getopt(sys.argv[1:], "dvh")
    for opt, arg in opts:
        if opt == "-d":
            DAEMON_FLAG = True
        if opt == "-v":
            VERBOSE = True
        elif opt == "-h":
            usage()
            sys.exit(0)

    if DAEMON_FLAG:
        daemonize(PID_FILE)

    # turn on logging for debug messages
    if VERBOSE:
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.DEBUG,
            format=LOG_FORMAT
            )
    else:
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.INFO,
            format=LOG_FORMAT
            )

    logging.getLogger().addHandler(logging.StreamHandler())
    logging.info("verbose %s", str(VERBOSE))

    # make updater
    updater_daemon = LinuxUpdaterDaemon(WORKING_DIR, FILE_CACHE_DIR)

    # set up dbus wrapper
    bus = SystemBus()
    bus.publish(DBUS_INTERFACE_NAME, updater_daemon)
    loop = GLib.MainLoop()

    try:
        loop.run()
    except KeyboardInterrupt:
        updater_daemon.quit()
        loop.quit()

    if DAEMON_FLAG is True:
        os.remove(PID_FILE)  # clean up daemon


if __name__ == "__main__":
    main()

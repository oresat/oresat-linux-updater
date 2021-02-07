"""Main for the OreSat Linux updater daemon.

Handles all arguement parsing, daemonizing, and log configuration.
"""

import sys
import os
import logging
from argparse import ArgumentParser
from logging.handlers import SysLogHandler
from pydbus import SystemBus
from gi.repository import GLib
from oresat_linux_updater.dbus_server import DBusServer, DBUS_INTERFACE_NAME


CACHE_DIR = "/var/cache/oresat_linux_manager/"
WORK_DIR = "/var/lib/oresat_linux_manager/"


def _daemonize(pid_file: str):
    """Daemonize the process

    Parameters
    ----------
    pid_file: str
        The path to the pid file for the daemon.
    """

    # Check for a pidfile to see if the daemon is already running
    try:
        with open(pid_file, 'r') as fptr:
            pid = int(fptr.read().strip())
    except IOError:
        pid = None

    if pid:
        sys.stderr.write("pid file {0} already exist".format(pid_file))
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
    stdin = open(os.devnull, 'r')
    stdout = open(os.devnull, 'a+')
    stderr = open(os.devnull, 'a+')

    os.dup2(stdin.fileno(), sys.stdin.fileno())
    os.dup2(stdout.fileno(), sys.stdout.fileno())
    os.dup2(stderr.fileno(), sys.stderr.fileno())

    pid = str(os.getpid())
    with open(pid_file, 'w+') as fptr:
        fptr.write(pid + '\n')


def main():
    """The main for the oresat linux updater daemon"""

    ret = 0
    pid_file = "/run/oresat-linux-updaterd.pid"

    parser = ArgumentParser()
    parser.add_argument("-d", "--daemon", action="store_true",
                        help="daemonize the process")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="enable debug log messaging")
    parser.add_argument("-w", "--work-dir", dest="work_dir",
                        default=WORK_DIR,
                        help="override the working directory")
    parser.add_argument("-c", "--cache-dir", dest="cache_dir",
                        default=CACHE_DIR,
                        help="override the update archive cache directory")
    args = parser.parse_args()

    if args.daemon:
        _daemonize(pid_file)
        log_handler = SysLogHandler(address="/dev/log")
    else:
        log_handler = logging.StreamHandler(sys.stderr)

    # turn on logging for debug messages
    if args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(level=level, handlers=[log_handler])

    log = logging.getLogger('oresat-linux-updater')

    # make updater
    updater = DBusServer(args.work_dir, args.cache_dir, log)

    # set up dbus wrapper
    bus = SystemBus()
    bus.publish(DBUS_INTERFACE_NAME, updater)
    loop = GLib.MainLoop()

    try:
        updater.run()
        loop.run()
    except KeyboardInterrupt:
        updater.quit()
        loop.quit()
    except Exception as exc:  # this should not happen
        log.critical(exc)
        updater.quit()
        loop.quit()
        ret = 1

    if args.daemon:
        os.remove(pid_file)  # clean up daemon

    return ret

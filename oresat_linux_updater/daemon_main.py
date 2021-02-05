"""Main for the oresat linux updater daemon.

Handles all arguement parsing, forking, log handling.
"""

import sys
import os
import logging
from argparse import ArgumentParser
from logging.handlers import SysLogHandler
from pydbus import SystemBus
from gi.repository import GLib
from daemon import Daemon, DBUS_INTERFACE_NAME


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


def usage():
    """Print the arguement usage message"""
    message = """
        usage:\n
        python3 -m oresat_linux_updater

        flags
        -d : to run as a process.
        -v : to on verbose logging.
        -h : this message.
        """
    print(message)


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
    updater_daemon = Daemon(args.work_dir, args.cache, log)

    # set up dbus wrapper
    bus = SystemBus()
    bus.publish(DBUS_INTERFACE_NAME, updater_daemon)
    loop = GLib.MainLoop()

    try:
        updater_daemon.start()
        loop.run()
    except KeyboardInterrupt:
        updater_daemon.quit()
        loop.quit()
    except Exception as exc:
        log.critical(exc)
        updater_daemon.quit()
        loop.quit()
        ret = 1

    if args.daemon:
        os.remove(pid_file)  # clean up daemon

    return ret


if __name__ == "__main__":
    main()

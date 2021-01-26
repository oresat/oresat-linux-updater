"""Main for the linux updater"""

import sys
import os
import getopt
import logging
from pydbus import SystemBus
from gi.repository import GLib
from logging.handlers import SysLogHandler
from oresat_linux_updater.updater_daemon import UpdaterDaemon, \
        DBUS_INTERFACE_NAME


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
    pid_file = "/run/oresat-linux-updaterd.pid"
    daemon_flag = False
    verbose = False

    opts, _ = getopt.getopt(sys.argv[1:], "dvh")
    for opt, _ in opts:
        if opt == "-d":
            daemon_flag = True
        if opt == "-v":
            verbose = True
        elif opt == "-h":
            usage()
            sys.exit(0)

    if daemon_flag:
        _daemonize(pid_file)
        log_handler = SysLogHandler(address="/dev/log")
    else:
        log_handler = logging.StreamHandler(sys.stderr)

    # turn on logging for debug messages
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(level=level, handlers=[log_handler])

    log = logging.getLogger('oresat-linux-updater')

    # make updater
    updater_daemon = UpdaterDaemon("/tmp/", "/var/cache/", log)

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

    if daemon_flag:
        os.remove(pid_file)  # clean up daemon

    return 0

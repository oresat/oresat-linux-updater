"""OreSat Linux Updater"""

MAJOR = 0
MINOR = 1
PATCH = 0

APP_NAME = "oresat-linux-updater"
APP_DESCRIPTION = "A quick wrapper daemon for apt on oresat linux boards."
APP_VERSION = "{}.{}.{}".format(MAJOR, MINOR, PATCH)
APP_AUTHOR = "Ryan Medick"
APP_EMAIL = "rmedick@pdx.edu"
APP_URL = "https://github.com/oresat/oresat-linux-updater"
APP_LICENSE = "GPL-3.0"

FILE_CACHE_DIR = "/var/cache/" + APP_NAME + "/"
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
LOG_FILE = "/var/log/" + APP_NAME + ".log"
PID_FILE = "/run/oresat-updaterd.pid"
WORKING_DIR = "/tmp/" + APP_NAME + "/"

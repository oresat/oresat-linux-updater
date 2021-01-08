#!/usr/bin/env python3
"""A script for starting a update with a local update archive"""

import argparse
import shutil
import os
from pydbus import SystemBus

APP_NAME = "oresat-linux-updater"
FILE_CACHE_DIR = "/var/cache/" + APP_NAME + "/"
INTERFACE_NAME = "org.oresat.update"

parser = argparse.ArgumentParser()
parser.add_argument("filepath", type=str, help="path to file to install")
args = parser.parse_args()

# move file to cache
filename = os.path.basename(args.filepath)
shutil.copyfile(args.filepath,  FILE_CACHE_DIR + filename)

# start update
bus = SystemBus()
updater = bus.get(INTERFACE_NAME)
updater.Update()

# OreSat Linux Updater
[![License](https://img.shields.io/github/license/oresat/oresat-linux-updater)](./LICENSE)
[![Issues](https://img.shields.io/github/issues/oresat/oresat-linux-updater)](https://github.com/oresat/oresat-linux-updater/issues)
![Unit Tests](https://github.com/oresat/oresat-linux-updater/workflows/oresat-linux-updater/badge.svg)

This is a daemon available on on all OreSat Linux board and will allow any the
board to update/patched through a archive file over a dbus interface.
The archive file can contain *.deb packages, bash scripts, and will have a
instructions.txt file to define the order deb packages are installed, remove,
or bash scripts are ran.

## Dependacies
- `sudo apt install python3 python3-pydbus python3-apt`

## Usage
- `python3 -m src/oresat_updaterd` To run as a process
- `python3 -m src/oresat_updaterd -h` For help output
- `python3 -m src/oresat_updaterd -d` To run as a daemon
- `python3 -m src/oresat_updaterd -v` Turn on verbose logging

## Building oresat Debian package
- `sudo apt install python3-stdeb`
- `python3 setup.py --command-packages=stdeb.command bdist_deb`

## Unit Tests
- `PYTHONPATH=".:src/" pytest tests` or `PYTHONPATH=".:src/" pytest-3 tests`

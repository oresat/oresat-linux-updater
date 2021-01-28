# OreSat Linux Updater

[![License](https://img.shields.io/github/license/oresat/oresat-linux-updater)](./LICENSE)
![Pytest](https://github.com/oresat/oresat-linux-updater/workflows/Pytest/badge.svg)
[![Issues](https://img.shields.io/github/issues/oresat/oresat-linux-updater)](https://github.com/oresat/oresat-linux-updater/issues)

This is a daemon available on on all OreSat Linux board and will allow any the
board to update/patched through a archive file over a dbus interface.
The archive file can contain *.deb packages, bash scripts, and will have a
instructions.txt file to define the order deb packages are installed, remove,
or bash scripts are ran.

## Dependacies

- `$ sudo apt install python3 python3-pydbus python3-apt libsystemd-dev`

## Building OreSast Debian package

- `$ dpkg-buildpackage -uc -us`
- This will produce `../oresat-linux-updater_*_all.deb`  

## Usage

- If install as a Debian package: `$ sudo systemctl start oresat-updaterd`
- From repo: `$ sudo python3 -m oresat_linux_updater`
- flags:
  - `-h` For help output
  - `-d` To run as a daemon
  - `-v` Turn on verbose logging

## Unit Tests

- Requires `python3-pytest`
- `$ pytest tests/` or `$ pytest-3 tests/`

## Docs

- Requires `python3-sphinx python3-sphinx-rtd-theme`
- `$ make -C docs/`
- Then open `docs/build/html/index.html` in a browser

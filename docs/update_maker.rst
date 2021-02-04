Update Maker
============
A shell script for making update files for the Oresat Linux Updater.

.. note:: It requries python3-apt as all OreSat Linux boards use Debian.

Shell
-----

Start it with:

.. code-block::

    $ olu-update-maker <board>

.. note:: As this is using a local dpkg status file `sudo` is not requried.

Commands

- `add-pkg` - Add debian packages.
- `remove-pkg` - Remove debian packages.
- `purge-pkg` - Purge debian packages.
- `add-bash` - Add bash scripts.

How it works
------------
It uses a local dpkg status file.

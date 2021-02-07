.. _glossary:

=======================
 Glossary of Terms Used
=======================

.. glossary::
    :sorted:

    OreSat
        PSAS's open source CubeSat. See https://www.oresat.org/

    D-Bus
        Inter-process communication system provided by systemd. See 
        https://www.freedesktop.org/wiki/Software/dbus/

    Daemon
        Long running, background process on Linux.

    OreSat Linux Manager (OLM)
        The front end daemon for all OreSat Linux boards.
        It converts CANopen message into DBus messages and vice versa. See
        https://github.com/oresat/oresat-linux-manager
    
    Update Archive
        A tar file used by the OreSat Linux updater daemon to update the board
        it is running on. It will contain deb package files and bash script.
        These will be made the the Updater Maker.

    Status Archive
        A tar file with two status files produced by the OreSat Linux updater.
        One with a JSON list of the update archive in OreSat Linux updater's
        cache and the other will be a copy of dpkg status file. The Update
        Maker will uses these to make future update archives.

    OreSat Linux Updater
        The common daemon found on all OreSat Linux boards, that handles
        updating the board with update archives.

    dpkg
        The low level package manager for install and removing packages on
        Debian Linux. APT is build ontop of it.

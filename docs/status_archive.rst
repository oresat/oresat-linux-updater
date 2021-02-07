Status Archive
==============

A status archive is a .tar.xz archive file that contains two files; a 
olu-status txt file and dpkg-status txt file. The oresat_linux_updater daemon
will make this if the MakeStatusFile dbus method is called. After every update,
a OLU status file should be made and sent to the ground station, so future
update can be made. The OLU status tar files will be around 100KiB.

OLU Status txt File
-------------------

This file will contain a JSON list of update archive files that are in the
cache and are available to be installed.

.. note:: If the cache is empty the status txt file will contain "`null`".


**Example OLU status file**::
    
    [
        "gps_update_1612392143.tar.xz",
        "gps_update_1612381721.tar.xz"
    ]

DPKG Status txt File
--------------------

A copy of the dpkg status file (`/var/lib/dpkg/status`) that will be used by the
update maker to make future updates to the board.

**Example dpkg status file**::

    Package: adduser
    Status: install ok installed
    Priority: important
    Section: admin
    Installed-Size: 849
    Maintainer: Debian Adduser Developers <adduser@packages.debian.org>
    Architecture: all
    Multi-Arch: foreign
    Version: 3.118
    Depends: passwd, debconf (>= 0.5) | debconf-2.0
    Suggests: liblocale-gettext-perl, perl
    Conffiles:
     /etc/deluser.conf 773fb95e98a27947de4a95abb3d3f2a2
    Description: add and remove users and groups
     This package includes the 'adduser' and 'deluser' commands for creating
     and removing users.
     .
      - 'adduser' creates new users and groups and adds existing users to
        existing groups;
      - 'deluser' removes users and groups and removes users from a given
        group.
     .
     Adding users with 'adduser' is much easier than adding them manually.
     Adduser will choose appropriate UID and GID values, create a home
     directory, copy skeletal user configuration, and automate setting
     initial values for the user's password, real name and so on.
     .
     Deluser can back up and remove users' home directories
     and mail spool or all the files they own on the system.
     .
     A custom script can be executed after each of the commands.

    Package: apt
    Status: install ok installed
    Priority: required
    Section: admin
    Installed-Size: 3509
    Maintainer: APT Development Team <deity@lists.debian.org>
    Architecture: armhf
    Version: 1.8.2.2
    Replaces: apt-transport-https (<< 1.5~alpha4~), apt-utils (<< 1.3~exp2~)
    Provides: apt-transport-https (= 1.8.2.2)
    Depends: adduser, gpgv | gpgv2 | gpgv1, debian-archive-keyring, libapt-pkg5.0 (>= 1.7.0~alpha3~), libc6 (>= 2.15), libgcc1 (>= 1:3.5), libgnutls30 (>= 3.6.6), libseccomp2 (>= 1.0.1), libstdc++6 (>= 5.2)
    Recommends: ca-certificates
    Suggests: apt-doc, aptitude | synaptic | wajig, dpkg-dev (>= 1.17.2), gnupg | gnupg2 | gnupg1, powermgmt-base
    Breaks: apt-transport-https (<< 1.5~alpha4~), apt-utils (<< 1.3~exp2~), aptitude (<< 0.8.10)
    Conffiles:
     /etc/apt/apt.conf.d/01autoremove 76120d358bc9037bb6358e737b3050b5
     /etc/cron.daily/apt-compat 49e9b2cfa17849700d4db735d04244f3
     /etc/kernel/postinst.d/apt-auto-removal 4ad976a68f045517cf4696cec7b8aa3a
     /etc/logrotate.d/apt 179f2ed4f85cbaca12fa3d69c2a4a1c3
    Description: commandline package manager
     This package provides commandline tools for searching and
     managing as well as querying information about packages
     as a low-level access to all features of the libapt-pkg library.
     .
     These include:
      * apt-get for retrieval of packages and information about them
        from authenticated sources and for installation, upgrade and
        removal of packages together with their dependencies
      * apt-cache for querying available information about installed
        as well as installable packages
      * apt-cdrom to use removable media as a source for packages
      * apt-config as an interface to the configuration settings
      * apt-key as an interface to manage authentication keys


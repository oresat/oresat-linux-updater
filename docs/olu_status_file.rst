Updater Status Tar File
=======================

A OLM status is a .tar.xz archive file that contains two files; a olu-status
txt file and dpkg-status txt file. The oresat_linux_updater daemon will make
this if the MakeStatusFile dbus method is called. After every update, a OLU
status file should be made and sent to the ground station, so future update can
be made. The OLU status tar files will be around 100KB.

OLU Status txt File
-------------------

This file will contain a JSON list of update archive files that are in the
cache and are available to be installed.

.. note:: If the cache is empty the status txt file will contain "`null`".


**Example**::
    
    [
        "gps_update_2021-10-03-14-30-27.tar.xz",
        "gps_update_2021-11-21-05-10-19.tar.xz",
    ]

DPKG Status txt File
--------------------

A copy of the dpkg status file (`/var/lib/dpkg/status`) that will be used by the
updater maker script.

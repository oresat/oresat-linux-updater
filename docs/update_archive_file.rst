Update Archive Files
====================

An update file is tar file that will be used by the OreSat Linux Updater
daemon to update the Linux board the daemon is running on. The update maker
will be used to generate these files.

Compression
-----------

Update files are a tar file compressed with xz. xz is used as it offers a great
compression ratio and the extra compression time doesn't matter, since the update
file will be generated on a ground station server.

Tar Name
---------

The file name will follow filename standards for oresat-linux-manager (OLM)
with the keyword set to "update". See
https://oresat-linux.readthedocs.io/en/latest/standards/file-transfer.html
for more info on OLM file name standards.

**Example, a update to the GPS board**::

   gps_update_1612392143.tar.xz

The date field in the filename will be used to determine the next file to used
as the oldest file is always run first.

Tar Contents
-------------

The update file will **always** include a instructions.txt file. It can also
include deb files (debian package files), bash script, and/or files to be used
by bash scripts as needed.

**Example contents of a update archive**::

    instructions.txt
    package1.deb
    package2.deb
    package3.deb
    bash_script1.sh
    bash_script2.sh
    bash_script3.sh
    bash_script2_external_file

instructions.txt
----------------

instruction.txt contatins a JSON string with with a list of instruction 
dictionaries with `type` and `items` fields. The instructions will be run in
order. 

.. autoclass:: oresat_linux_updater.instruction.InstructionType
   :members:
   :member-order: bysource
   :noindex:

**Example instructions.txt**::

    [
        {
            "type": "DPKG_INSTALL",
            "items": ["package1.deb"]
        },
        {
            "type": "BASH_SCIPT",
            "items": ["bash_script1.sh", "bash_script2.sh"]
        },
        {
            "type": "DPKG_INSTALL",
            "items": ["package2.deb", "package3.deb"]
        },
        {
            "type": "DPKG_REMOVE",
            "items": ["package4"]
        },
        {
            "type": "BASH_SCIPT",
            "items": ["bash_script3.sh"]
        }
        {
            "type": "DPKG_PURGE",
            "items": ["package5", "package6"]
        },
        {
            "type": "SUPPORT_FILE",
            "items": ["bash_script2_external_file"]
        }
    ]

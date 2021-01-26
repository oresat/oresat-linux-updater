Update Archive Files
====================

Update archive files should be a .tar.xz archive file and follow the file
transfer filename format with the keyword "update". The date field in the
filename will be used to determine the next file to use as the oldest file is
always used.

**Example, a update to the GPS board**::

   gps_update_2021-10-03-14-30-27.tar.xz

An update archive should contant deb files, bash scripts, files used by 
bash script, and will **always** include a instructions.txt file. If there is
no instructions.txt in the archive file, the and all following update will be 
deleted and the error message will be sent to OLM.

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
dictionaries with type and items fields. The instructions will be run in order.

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
        },
    ]

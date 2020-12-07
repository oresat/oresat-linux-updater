Archive File
============
Archive files name should be in the format of
board-name_update_YYYY-MM-dd-hh-mm-ss.tar.gz. Example:
startracker_update_2020-02-10-14-30-23.tar.gz aka a star tracker update
archive file made on Feburary 10th 2020 at 14:30:23 UTC.

Archive file contents
---------------------
Tar gz archive file with deb package, bash scripts, and an instructions.txt
file. All archive file must have instructions.txt.

Example archive file contents: ::

    instructions.txt
    package1.deb
    package2.deb
    package3.deb
    bash_script1.sh
    bash_script2.sh
    bash_script3.sh


instructions.txt format
-----------------------
instruction.txt contatins a JSON string with with a list of instruction_types
and instruction_item. Where instruction_types can be install_pkg, remove_pkg,
or bash_script. The instructions will be run in order.

Example instructions.txt contents: ::

    [
        {
            "type": "install_pkg",
            "item": "package1.deb"
        },
        {
            "type": "bash_script",
            "item": "bash_script1.sh"
        },
        {
            "type": "install_pkg",
            "item": "package2.deb"
        },
        {
            "type": "install_pkg",
            "item": "package3.deb"
        },
        {
            "type": "bash_script",
            "item": "bash_script2.sh"
        },
        {
            "type": "remove_pkg",
            "item": "package4"
        },
        {
            "type": "bash_script",
            "item": "bash_script3.sh"
        }
    ]


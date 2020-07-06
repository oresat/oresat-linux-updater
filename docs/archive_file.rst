Archive File
============
Archive files name should be in the formate of
board_name-update-YYYY-MM-dd-hh-mm-ss.tar.gz. Example:
star_tracker-update-2020-02-10-14-30-23.tar.gz aka a start tracker update
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
instruction.txt contatins a JSON string with with a list of instructions and
instruction_types. Where instruction_types can be install_pkg, remove_pkg, or
bash_script. The instructions will be run in order.

Example instructions.txt contents: ::

    [
        ["package1.deb", "install_pkg"],
        ["bash_script1.sh","bash_script"],
        ["package2.deb", "install_pkg"],
        ["package3.deb", "install_pkg"],
        ["bash_script2.sh","bash_script"],
        ["package4", "remove_pkg"],
        ["bash_script3.sh","bash_script"]
    ]


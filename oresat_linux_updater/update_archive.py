"""
Update Archive
==============

An update archive is tar file that will be used by the OreSat Linux Updater
daemon to update the Linux board the daemon is running on. The update maker
will be used to generate these files.

Compression
-----------

Update files are a tar file compressed with xz. xz is used as it offers a great
compression ratio and the extra compression time doesn't matter, since the
update archive will be generated on a ground station server.

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

The update archive will **always** include a instructions.txt file. It can also
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
            "items": ["bash_script1.sh"]
        },
        {
            "type": "BASH_SCIPT",
            "items": ["bash_script2.sh"]
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
"""

import json
import tarfile
from os import remove
from os.path import abspath, basename, isfile
from oresat_linux_updater.instruction import Instruction, InstructionError, \
        InstructionType, INSTRUCTIONS_WITH_FILES
from oresat_linux_updater.olm_file import OLMFile

INST_FILE = "instructions.txt"
"""The instructions file that is always in a OreSat Linux update archive. It
defines the order instructions are ran in and how it is ran.
"""


class UpdateArchiveError(Exception):
    """An error occurred when creating or extracting a update archive."""


def write_instructions_file(inst_list: list, path_dir) -> str:
    """Makes the instructions file from a instructions list.

    Parameters
    ----------
    inst_list: list
        A list of Instructions objects.
    path_dir: str
        The directory to make the tar in.

    Raises
    ------
    ValueError
        Invalid inst_list.

    Returns
    -------
    str
        Absolute path to the new instructions file.
    """

    inst_data = []
    path_dir = abspath(path_dir) + "/"
    inst_file = path_dir + INST_FILE

    for inst in inst_list:
        if inst.type in INSTRUCTIONS_WITH_FILES:
            items = []
            for i in inst.items:
                items.append(basename(i))
        else:
            items = inst.items

        inst_data.append({"type": inst.type.name, "items": items})

    # make instructions file
    with open(inst_file, "w") as fptr:
        fptr.write(json.dumps(inst_data))

    return inst_file


def read_instructions_file(inst_file: str, work_dir: str) -> str:
    """Open the instructions file.

    Parameters
    ----------
    update_archive: str
        Path to the update archive.
    work_dir: str
        The directory to open the tarfile in.

    Raises
    ------
    UpdateArchiveError
        Invalid update instruction JSON or

    Returns
    -------
    list
        A list of Instructions.
    """

    inst_list = []
    work_dir = abspath(work_dir) + "/"
    inst_file = abspath(inst_file)

    try:
        with open(inst_file, "r") as fptr:
            inst_list_raw = json.load(fptr)
    except json.JSONDecodeError:
        msg = "Invalid instructions JSON in {}".format(inst_file)
        raise UpdateArchiveError(msg)

    # add path to all files
    for inst_raw in inst_list_raw:
        try:
            i_type = InstructionType[inst_raw["type"]]
            i_items = inst_raw["items"]
        except (TypeError, KeyError):
            msg = "Instructions file JSON was formatted incorrectly"
            raise UpdateArchiveError(msg)

        if i_type in INSTRUCTIONS_WITH_FILES:
            items = []
            for item in i_items:
                items.append(work_dir + item)
        else:
            items = i_items

        try:
            inst = Instruction(i_type, items)  # this will valid the type
        except InstructionError:
            msg = "Instructions file JSON was formatted incorrectly"
            raise UpdateArchiveError(msg)

        inst_list.append(inst)

    return inst_list


def create_update_archive(board: str, inst_list: dict, work_dir: str,
                          consume_files=True) -> str:
    """Makes the tar from a list of instructions. This will consume all files
    if a valid update archive is made.

    Parameters
    ----------
    board: str
        The board the update is for.
    inst_list: list
        A list of instruction dictionaries.
    work_dir: str
        The directory to make the tar in.
    consume: bool
        A flag if the file should be consumed.

    Raises
    ------
    InstructionError
        Invalid inst_list.

    Returns
    -------
    str
        Absolute path to the new update archive.
    """

    files = []
    work_dir = abspath(work_dir) + "/"
    update = OLMFile(board=board, keyword="updated", ext=".tar.xz")

    inst_file = write_instructions_file(inst_list, work_dir)
    files.append(inst_file)

    for inst in inst_list:
        if inst.type in INSTRUCTIONS_WITH_FILES:
            files += inst.items

    for item in files:
        if not isfile(item):
            raise UpdateArchiveError("missing file {}".format(item))

    # make tar
    with tarfile.open(work_dir + update.name, "w:xz") as tar:
        for item in files:
            tar.add(item, arcname=basename(item))

    if consume_files:
        # delete files
        for item in files:
            remove(item)

    return work_dir + update.name


def extract_update_archive(update_archive: str, work_dir: str) -> str:
    """Open the update archive file.

    Parameters
    ----------
    update_archive: str
        Path to the update archive.
    work_dir: str
        The directory to open the tarfile in.

    Raises
    ------
    UpdateArchiveError
        Invalid update archive.

    Returns
    -------
    str
        The contents of the instructions file.
    """

    work_dir = abspath(work_dir) + "/"

    if not is_update_archive(update_archive):
        msg = "Update file does not follow OLM filename standards"
        raise UpdateArchiveError(msg)

    try:
        with tarfile.open(update_archive, "r:xz") as tptr:
            tptr.extractall(work_dir)
    except tarfile.TarError:
        raise UpdateArchiveError("Invalid update archive")

    try:
        inst_list = read_instructions_file(work_dir + INST_FILE, work_dir)
    except InstructionError as exc:
        raise UpdateArchiveError(str(exc))

    # check that all file were in tarfile
    for inst in inst_list:
        if inst.type in INSTRUCTIONS_WITH_FILES:
            for item in inst.items:
                if not isfile(item):
                    raise UpdateArchiveError("Missing file {}".format(item))

    return inst_list


def is_update_archive(update_archive: str) -> bool:
    """Check to see if the input is a valid update archive.

    Parameters
    ----------
    update_archive: str
        Path to the update archive.

    Returns
    -------
    bool
        True the file name is valid or False if it is invalid.
    """

    try:
        fptr = OLMFile(load=update_archive)
    except Exception:
        return False

    if fptr.keyword == "update" and fptr.extension == ".tar.xz":
        return True

    return False

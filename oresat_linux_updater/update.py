"""Everything need to make and extract an OreSat Linux update file and its
instructions file
"""

import json
import tarfile
from os import remove
from os.path import abspath, basename, isfile
from oresat_linux_updater.instruction import Instruction, InstructionError, \
        InstructionType, INSTRUCTIONS_WITH_FILES
from oresat_linux_updater.olm_file import OLMFile

INST_FILE = "instructions.txt"
"""The instructions file that is always in a OreSat Linux update. It defines
the order instructions are ran in.
"""


class UpdateError(Exception):
    """An error occurred when creating or extracting a update file."""


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
        print(inst)
        if inst.type in INSTRUCTIONS_WITH_FILES:
            items = []
            for i in inst.items:
                items.append(basename(i))
        else:
            items = inst.items

        inst_data.append({"type": inst.type.name, "items": items})

    # make instructions file
    with open(inst_file, "w") as fptr:
        json.dump(inst_data, fptr)

    return inst_file


def read_instructions_file(inst_file: str, work_dir: str) -> str:
    """Open the instructions file.

    Parameters
    ----------
    update_file: str
        Path to the update file.
    work_dir: str
        The directory to open the tarfile in.

    Raises
    ------
    UpdateError
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
        raise UpdateError("Invalid instructions JSON in {}".format(inst_file))

    # add path to all files
    for inst_raw in inst_list_raw:
        try:
            i_type = InstructionType[inst_raw["type"]]
            i_items = inst_raw["items"]
        except (TypeError, KeyError):
            msg = "Instructions file JSON was formatted incorrectly"
            raise UpdateError(msg)

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
            raise UpdateError(msg)

        inst_list.append(inst)

    return inst_list


def create_update_file(board: str, inst_list: dict, work_dir: str) -> str:
    """Makes the tar from a list of instructions. This will consume all files
    if a valid update file is made.

    Parameters
    ----------
    board: str
        The board the update is for.
    inst_list: list
        A list of instruction dictionaries.
    work_dir: str
        The directory to make the tar in.

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
            raise UpdateError("missing file {}".format(item))

    # make tar
    with tarfile.open(work_dir + update.name, "w:xz") as tar:
        for item in files:
            tar.add(item, arcname=basename(item))

    # delete files
    for item in files:
        remove(item)

    return work_dir + update.name


def extract_update_file(update_file: str, work_dir: str) -> str:
    """Open the update archive file.

    Parameters
    ----------
    update_file: str
        Path to the update file.
    work_dir: str
        The directory to open the tarfile in.

    Raises
    ------
    UpdateError
        Invalid update file.

    Returns
    -------
    str
        The contents of the instructions file.
    """

    work_dir = abspath(work_dir) + "/"

    if not is_update_file(update_file):
        raise UpdateError("Update file does not follow OLM filename standards")

    try:
        with tarfile.open(update_file, "r:xz") as tptr:
            tptr.extractall(work_dir)
    except tarfile.TarError:
        raise UpdateError("Invalid update file")

    try:
        inst_list = read_instructions_file(work_dir + INST_FILE, work_dir)
    except InstructionError as exc:
        raise UpdateError(str(exc))

    # check that all file were in tarfile
    for inst in inst_list:
        if inst.type in INSTRUCTIONS_WITH_FILES:
            for item in inst.items:
                if not isfile(item):
                    raise UpdateError("Missing file {}".format(item))

    return inst_list


def is_update_file(update_file: str) -> bool:
    """Check to see if the input is a valid update file.

    Returns
    -------
    bool
        True the file name is valid or False if it is invalid.
    """

    try:
        fptr = OLMFile(load=update_file)
    except Exception:
        return False

    if fptr.keyword == "update" and fptr.extension == ".tar.xz":
        return True

    return False

"""tests for the classes in instruction"""

import pytest
from oresat_linux_updater.instruction import InstructionType, Instruction
from oresat_linux_updater.instructions_list import InstructionsList, \
        InstructionsTxtError
from .common import TEST_FILE_DIR


@pytest.fixture
def instructions_list():
    """make the InstructionsList object"""
    return InstructionsList()


def test_json_str(instructions_list):
    """Test the json_str method"""

    inst1 = Instruction(InstructionType.DPKG_INSTALL, ["test1"])
    inst2 = Instruction(InstructionType.DPKG_INSTALL, ["test2"])

    instructions_list.append(inst1)
    instructions_list.append(inst2)

    instructions_list.json_str


def test_files_needed(instructions_list):
    """Test the files_needed function"""

    inst1 = Instruction(InstructionType.DPKG_INSTALL, ["test1"])
    inst2 = Instruction(InstructionType.DPKG_INSTALL, ["test2"])

    instructions_list.append(inst1)
    instructions_list.append(inst2)

    assert ["test1", "test2"] == instructions_list.files_needed()


def test_read_file():
    """Test making a InstructionsList file from a file"""

    # valid file
    InstructionsList(TEST_FILE_DIR + "instructions1.txt")

    # invalid file - invalid contents
    with pytest.raises(InstructionsTxtError):
        InstructionsList(TEST_FILE_DIR + "instructions2.txt")

    # invalid file - invalid type
    with pytest.raises(InstructionsTxtError):
        InstructionsList(TEST_FILE_DIR + "instructions3.txt")

    # invalid file - invalid json
    with pytest.raises(InstructionsTxtError):
        InstructionsList(TEST_FILE_DIR + "instructions4.txt")

    # invalid file - invalid json
    with pytest.raises(InstructionsTxtError):
        InstructionsList(TEST_FILE_DIR + "instructions5.txt")

    # no file
    with pytest.raises(FileNotFoundError):
        InstructionsList(TEST_FILE_DIR + "instructions6.txt")

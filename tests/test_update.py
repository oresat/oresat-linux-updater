"""tests for the UpdaterDaemon class"""

import pytest
from oresat_linux_updater.instruction import Instruction, InstructionType
from oresat_linux_updater.update import UpdateError, read_instructions_file, \
        extract_update_file, write_instructions_file, create_update_file
from .common import TEST_WORK_DIR, TEST_INST_FILE1, TEST_INST_FILE2, \
        TEST_INST_FILE3, TEST_INST_FILE4, TEST_INST_FILE5, TEST_UPDATE0, \
        TEST_UPDATE1, TEST_UPDATE2, TEST_UPDATE3, TEST_UPDATE4, TEST_UPDATE5, \
        TEST_UPDATE6, TEST_UPDATE7, TEST_UPDATE8, TEST_UPDATE9, \
        clear_test_work_dir, TEST_DEB_PKG1, TEST_DEB_PKG2, TEST_DEB_PKG1_NAME,\
        TEST_DEB_PKG2_NAME, TEST_BASH_SCRIPT


def test_read_instructions_file():
    """Test opening instructions file."""

    # valid instructions file

    read_instructions_file(TEST_INST_FILE1, TEST_WORK_DIR)

    # invalid instructions files

    with pytest.raises(UpdateError):
        read_instructions_file(TEST_INST_FILE2, TEST_WORK_DIR)

    with pytest.raises(UpdateError):
        read_instructions_file(TEST_INST_FILE3, TEST_WORK_DIR)

    with pytest.raises(UpdateError):
        read_instructions_file(TEST_INST_FILE4, TEST_WORK_DIR)

    with pytest.raises(UpdateError):
        read_instructions_file(TEST_INST_FILE5, TEST_WORK_DIR)


def test_write_instructions_file():
    """Test writing a instructions file."""

    inst_list1 = [
                Instruction(InstructionType.DPKG_INSTALL, [TEST_DEB_PKG1, TEST_DEB_PKG2]),
                Instruction(InstructionType.BASH_SCRIPT, [TEST_BASH_SCRIPT])
            ]

    write_instructions_file(inst_list1, TEST_WORK_DIR)
    clear_test_work_dir()


def test_extract_update_file():
    """Test opening updates files."""

    # valid updates

    clear_test_work_dir()
    extract_update_file(TEST_UPDATE0, TEST_WORK_DIR)

    clear_test_work_dir()
    extract_update_file(TEST_UPDATE1, TEST_WORK_DIR)

    clear_test_work_dir()
    extract_update_file(TEST_UPDATE2, TEST_WORK_DIR)

    # invalid updates

    clear_test_work_dir()
    with pytest.raises(FileNotFoundError):
        extract_update_file(TEST_UPDATE3, TEST_WORK_DIR)

    clear_test_work_dir()
    with pytest.raises(UpdateError):
        extract_update_file(TEST_UPDATE4, TEST_WORK_DIR)

    clear_test_work_dir()
    with pytest.raises(UpdateError):
        extract_update_file(TEST_UPDATE5, TEST_WORK_DIR)

    clear_test_work_dir()
    with pytest.raises(UpdateError):
        extract_update_file(TEST_UPDATE6, TEST_WORK_DIR)

    clear_test_work_dir()
    with pytest.raises(UpdateError):
        extract_update_file(TEST_UPDATE7, TEST_WORK_DIR)

    clear_test_work_dir()
    with pytest.raises(UpdateError):
        extract_update_file(TEST_UPDATE8, TEST_WORK_DIR)

    clear_test_work_dir()
    with pytest.raises(UpdateError):
        extract_update_file(TEST_UPDATE9, TEST_WORK_DIR)

    clear_test_work_dir()
    with pytest.raises(UpdateError):
        extract_update_file("invalid-file", TEST_WORK_DIR)


def test_create_update_file():
    """Test making a new update file."""

    inst_list1 = [
                Instruction(InstructionType.DPKG_INSTALL, [TEST_DEB_PKG1, TEST_DEB_PKG2]),
                Instruction(InstructionType.DPKG_REMOVE, [TEST_DEB_PKG1_NAME, TEST_DEB_PKG2_NAME]),
                Instruction(InstructionType.BASH_SCRIPT, [TEST_BASH_SCRIPT])
            ]

    inst_list2 = [
                Instruction(InstructionType.DPKG_INSTALL, ["invalid1", "invalid2"]),
            ]

    create_update_file("test", inst_list1, TEST_WORK_DIR)

    with pytest.raises(UpdateError):
        create_update_file("test", inst_list2, TEST_WORK_DIR)

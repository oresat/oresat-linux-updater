"""tests for the Instruction class"""

import pytest
from oresat_linux_updater.instruction import Instruction, InstructionType, \
        InstructionError, _bash_command
from .common import LOGGER, TEST_DEB_PKG1, TEST_DEB_PKG2, TEST_DEB_PKG1_NAME, \
        TEST_DEB_PKG2_NAME, TEST_BASH_SCRIPT


def test_bash_command():
    """Test _bash_command"""

    _bash_command("ls", LOGGER)

    with pytest.raises(InstructionError):
        _bash_command("abcd", LOGGER)


def test_run_instruction():
    """Test opening instructions file."""

    # bash script
    Instruction(InstructionType.BASH_SCRIPT, [TEST_BASH_SCRIPT]).run(LOGGER)
    with pytest.raises(InstructionError):
        Instruction(InstructionType.BASH_SCRIPT, ["abcd"]).run(LOGGER)

    # single install/remove/purge
    with pytest.raises(InstructionError):
        Instruction(InstructionType.DPKG_INSTALL, ["abcd"]).run(LOGGER)
    with pytest.raises(InstructionError):
        Instruction(InstructionType.DPKG_INSTALL, [TEST_DEB_PKG2]).run(LOGGER)
    Instruction(InstructionType.DPKG_INSTALL, [TEST_DEB_PKG1]).run(LOGGER)
    Instruction(InstructionType.DPKG_INSTALL, [TEST_DEB_PKG2]).run(LOGGER)
    with pytest.raises(InstructionError):
        Instruction(InstructionType.DPKG_REMOVE, [TEST_DEB_PKG1_NAME]).run(LOGGER)
    Instruction(InstructionType.DPKG_PURGE, [TEST_DEB_PKG2_NAME]).run(LOGGER)
    Instruction(InstructionType.DPKG_REMOVE, [TEST_DEB_PKG1_NAME]).run(LOGGER)

    # multiple install/remove/purge
    Instruction(InstructionType.DPKG_INSTALL, [TEST_DEB_PKG1, TEST_DEB_PKG2]).run(LOGGER)
    Instruction(InstructionType.DPKG_REMOVE, [TEST_DEB_PKG1_NAME, TEST_DEB_PKG2_NAME]).run(LOGGER)
    Instruction(InstructionType.DPKG_REMOVE, [TEST_DEB_PKG1_NAME]).run(LOGGER)  # cleanup

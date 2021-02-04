"""Everything todo with update instructions."""

import logging
import subprocess
from enum import IntEnum, auto


class InstructionType(IntEnum):
    """All the valid instruction types for the instructions.txt file."""

    BASH_SCRIPT = 0
    """Run one or more bash scripts."""

    SUPPORT_FILE = auto()
    """One or more support files that will by used by a bash script"""

    DPKG_INSTALL = auto()
    """Install one or more packages with dpkg."""

    DPKG_REMOVE = auto()
    """Remove one or more packages with dpkg."""

    DPKG_PURGE = auto()
    """Purge one or more packages with dpkg."""


INSTRUCTIONS_WITH_FILES = [
        InstructionType.BASH_SCRIPT,
        InstructionType.SUPPORT_FILE,
        InstructionType.DPKG_INSTALL,
        ]
"""The list of instructions that require files."""


class InstructionError(Exception):
    """Invalid instruction."""


class Instruction():
    """Makes instruction dictionary.

    Parameters
    ----------
    i_type: str
        The type of instruction.
    i_items: list
        A list of str for the instruction. If it is a type in
        INSTRUCTIONS_WITH_FILES, it will be a list of absolute paths to files.
    """

    def __init__(self, i_type: InstructionType, i_items: list):
        if i_type not in InstructionType:
            raise InstructionError("Invalid instruction type")

        self._type = i_type
        self._items = i_items

        self._items_str = ""
        for item in self._items:
            self._items_str += " " + item

    def __repr__(self):
        return "{}: {}".format(self.__class__.__name__, self._type)

    def __str__(self):
        return "{}: {}".format(self._type, self._items)

    def run(self, log: logging.Logger):
        """Run all instructions. All stdout message will be logged with info
        level and all stderr messages will be logged with error level.

        Parameters
        ----------
        log: logging.Logger
            The logger to use to output stdin, stdout, stderr.

        Raises
        ------
        InstructionError
            Invalid instruction.
        """

        if self._type == InstructionType.BASH_SCRIPT:
            for item in self._items:
                _bash_command("bash " + item, log)
        elif self._type == InstructionType.DPKG_INSTALL:
            _bash_command("dpkg -i" + self._items_str, log)
        elif self._type == InstructionType.DPKG_REMOVE:
            _bash_command("dpkg -r" + self._items_str, log)
        elif self._type == InstructionType.DPKG_PURGE:
            _bash_command("dpkg -P" + self._items_str, log)

    @property
    def type(self):
        """str: The instruction type."""
        return self._type

    @property
    def items(self):
        """list: the items for the instruction."""
        return self._items


def _bash_command(command: str, log: logging.Logger) -> bool:
    """Run a bash command. All stdout message will be logged with info
    level and all stderr messages will be logged with error level.

    Parameters
    ----------
    command : str
        The bash command string to run.
    log: logging.Logger
        The logger to use to output stdin, stdout, stderr.

    Raises
    ------
    InstructionError
        Invalid instruction.
    """

    log.info(command)

    out = subprocess.run(command, capture_output=True, shell=True)

    if out.returncode != 0:
        for line in out.stderr.decode("utf-8").split("\n"):
            if len(line) != 0:
                log.error(line)

        raise InstructionError("Bash command failed!")

    for line in out.stdout.decode("utf-8").split("\n"):
        if len(line) != 0:
            log.info(line)

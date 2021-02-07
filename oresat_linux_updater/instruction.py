"""Everything todo with update instructions."""

import subprocess
from logging import Logger
from enum import IntEnum, auto


class InstructionType(IntEnum):
    """All the valid instruction types for the instructions.txt file."""

    BASH_SCRIPT = 0
    """Run a bash scripts."""

    SUPPORT_FILE = auto()
    """One or more support files that will by used by a bash script."""

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
    """Instruction for the OreSat Linux updater."""

    def __init__(self, i_type: InstructionType, i_items: list):
        """
        Parameters
        ----------
        i_type: InstructionType
            The type of instruction.
        i_items: list
            A list of :class:`str` for the instruction. If it is a
            :data:`InstructionType.BASH_SCRIPT` the list must be only have 1
            item.
        """

        if i_type not in InstructionType:
            raise InstructionError("Invalid instruction type")
        if len(i_items) == 0:
            raise InstructionError("i_items cannot be an empty list")
        if i_type == InstructionType.BASH_SCRIPT and len(i_items) != 1:
            msg = "bash script can only have list with a length of 1"
            raise InstructionError(msg)

        self._type = i_type
        self._items = i_items

        items_str = ""
        for item in self._items:
            items_str += " " + item

        if self._type == InstructionType.BASH_SCRIPT:
            self._bash_command = "bash " + self._items[0]
        elif self._type == InstructionType.SUPPORT_FILE:
            self._bash_command = ""
        if self._type == InstructionType.DPKG_INSTALL:
            self._bash_command = "dpkg -i" + items_str
        elif self._type == InstructionType.DPKG_REMOVE:
            self._bash_command = "dpkg -r" + items_str
        elif self._type == InstructionType.DPKG_PURGE:
            self._bash_command = "dpkg -P" + items_str

    def __repr__(self):
        return "{}: {}".format(self.__class__.__name__, self._type)

    def __str__(self):
        return "{}: {}".format(self._type, self._items)

    def run(self, log: Logger):
        """Run the instruction. All stdout message will be logged with info
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

        if self.bash_command != "":
            run_bash_command(self._bash_command, log)

    @property
    def type(self):
        """str: The instruction type."""

        return self._type

    @property
    def items(self):
        """list: The items for the instruction."""

        return self._items

    @property
    def bash_command(self):
        """str: The equivalent bash command for the instruction."""

        return self._bash_command


def run_bash_command(command: str, log: Logger) -> bool:
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

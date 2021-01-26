"""A class for making and reading instructions.txt file"""

import json
from enum import Enum, auto


class InstructionType(Enum):
    """All the valid instruction types for the instructions.txt file."""

    BASH_SCRIPT = auto()
    """Run one or more bash scripts."""

    SUPPORT_FILE = auto()
    """One or more support files that will by used by a bash script"""

    DPKG_INSTALL = auto()
    """Install one or more packages with dpkg."""

    DPKG_REMOVE = auto()
    """Remove one or more packages with dpkg."""

    DPKG_PURGE = auto()
    """Purge one or more packages with dpkg."""


class Instruction():
    """POD class for instruction in instructions.txt

    Attributes
    ----------
    type: InstructionType
        The type of instruction.
    items: list
        A list of object for the instruction.
    """

    def __init__(self, i_type: InstructionType, i_items: list):
        """
        Parameters
        ----------
        i_type: InstructionType
            The type of instruction.
        i_items: list
            A list of object for the instruction.
        """
        self.type = i_type
        self.items = i_items

    def __repr__(self) -> str:
        return "<{0} {1}>".format(self.__class__.__name__, self.type)

    def __str__(self):
        return "{} {}".format(self.type.name, self.items)


class InstructionEncoder(json.JSONEncoder):
    """A JSON encoder for Instruction class"""

    def default(self, obj):
        if isinstance(obj, Instruction):
            return {"type": obj.type.name, "items": obj.items}

        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

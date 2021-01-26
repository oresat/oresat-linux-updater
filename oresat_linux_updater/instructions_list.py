"""A class for making and reading instructions.txt file"""

import json
from collections import UserList
from oresat_linux_updater.instruction import Instruction, InstructionType, \
        InstructionEncoder


class InstructionsTxtError(Exception):
    """Invalid instructions.txt format"""


class InstructionsList(UserList):
    """Class for manipulating an archive file."""

    def __init__(self, filename=""):
        """
        Parameters
        ----------
        filename: str
            Optional. Will open the content of update file and load it.

        Raises
        ------
        FileNotFoundError
        InstructionsTxtError
        """

        super().__init__()

        self._i_types_w_files = [  # these type require the i_items files
                InstructionType.BASH_SCRIPT,
                InstructionType.SUPPORT_FILE,
                InstructionType.DPKG_INSTALL
                ]

        if filename != "":
            with open(filename) as fptr:
                instructions_str = fptr.read()

            try:
                temp = json.loads(instructions_str)
            except json.JSONDecodeError:
                msg = "invalid JSON in {}".format(filename)
                raise InstructionsTxtError(msg)

            # make a list of all instructions Enums as str
            i_types_dict = {}
            for i in InstructionType:
                i_types_dict[i.name] = i

            # validate list
            index = 0
            for i in temp:
                index += 1

                try:
                    i_type = i["type"]
                    i_items = i["items"]
                except KeyError:
                    raise InstructionsTxtError("invalid instructions dict")

                if i_type not in i_types_dict:
                    msg = "unknown type {}".format(i_type)
                    raise InstructionsTxtError(msg)

                if not isinstance(i_items, list):
                    msg = "items {} is not a list".format(index)
                    raise InstructionsTxtError(msg)

                self.data.append(Instruction(i_types_dict[i_type], i_items))

    def has_item(self, item: str) -> bool:
        """Check if item is in instructions"""

        ret = False

        for inst in self.data:
            if item in inst.items:
                ret = True
                break

        return ret

    def files_needed(self, filter=None) -> list:
        """Gets the list of files needed.

        Parameters
        ----------
        filter: InstructionType
            Optional, filter for a specific InstructionType.

        Raises
        ------
        InstructionsTxtError

        Returns
        -------
        list
            A list of files needed fot that filter.
        """

        ret = []

        if filter is None:  # no filter
            types = self._i_types_w_files
        elif filter in self._i_types_w_files:  # valid filter
            types = [filter]
        else:  # invalid filter
            msg = "Invalid instruction type filter {}".format(filter)
            raise InstructionsTxtError(msg)

        for i in self.data:
            if i.type in types:
                for j in i.items:
                    ret.append(j)
            else:
                msg = "Invalid instruction type filter {}".format(i.type.name)
                raise InstructionsTxtError(msg)

        return ret

    @property
    def json_str(self):
        """str: Gets the JSON str"""

        return json.dumps(self.data, cls=InstructionEncoder)

"""Fallow the file format for the OreSat Linux Manager."""

from os import uname
from os.path import basename
from time import time


class OLMFile():
    """A class that follows the OreSat Linux Manager file format.

    Can be used in list to sort a list of files following the
    oresat-linux-manager (OLM) filename standards. When used in a sorted list,
    the list will be order newest to oldest, so list.pop() can be used to get
    the oldest file in the list.
    """

    def __init__(self, load=None, board=None, keyword=None, ext=".txt"):
        """
        Parameters
        ----------
        load: str
            Path to the file. Used to make a OLMFile object from an existing
            file. Cannot be used in tandem with keyword.
        board: str
            The board name for the new file. Optional, can be used for new
            OLMFile object. If not set and keyword is set, the hostname will be
            used.
        keyword: str
            The keyword for the new file. Used to make new OLMFile object. Must
            be set unless board is set.
        ext: str
            The file extension. Optional, can be used for new OLMFile object.
            If not set ".txt" will be used.

        Raises
        ------
        ValueError
            If load and keyword are both set.
        FileNotFoundError
            If load is set to an invalid filepath.
        """
        if load is not None and keyword is not None:
            raise ValueError("Can't load a file and make a new file")

        if load is not None:  # load file
            self._name = basename(load)

            self._board = self.name.split("_")[0]
            self._keyword = self.name.split("_")[1]

            temp = self.name.split("_")[2]

            self._date = int(temp.split(".")[0])
            self._extension = temp[temp.find("."):]
        elif keyword is not None:  # hold data for new file
            if board is None:
                board = uname()[1]
            else:
                self._board = board

            self._keyword = keyword
            self._date = int(time())
            self._extension = ext
            self._name = board + "_" + keyword + "_" + str(self._date) + ext

    def __repr__(self):
        return "{} {}".format(self.__class__.__name__, self._name)

    def __str__(self):
        return self._name

    def __lt__(self, archive_file2):
        return archive_file2.date < self._date

    def __gt__(self, archive_file2):
        return archive_file2.date > self._date

    @property
    def name(self) -> str:
        """str: The full name for the file."""
        return self._name

    @property
    def board(self) -> str:
        """str: The board the file is for or from."""
        return self._board

    @property
    def keyword(self) -> str:
        """str: The keyword for the file, this is used by OLM to figure out what
        todo with the file.
        """
        return self._keyword

    @property
    def date(self) -> int:
        """int: The Unix time the file was made.
        """
        return self._date

    @property
    def extension(self) -> str:
        """str: The file extension."""
        return self._extension

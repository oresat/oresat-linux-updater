"""File Cache"""

import re
import os
import shutil
import json
from pathlib import Path



class UpdateArchiveCache():
    """Used to store the update archive files sent to the linux updater."""

    def __init__(self, cache_dir: str):
        """
        Parameters
        ----------
        cache_dir: str
            The path to a directory for the cache.
        """

        # filename regex
        self._file_regex = re.compile(r"\w*_\w*_\d*\.tar\.xz$")

        # If the directory does not make it
        Path(cache_dir).mkdir(parents=True, exist_ok=True)

        # a / to end of cache_dir_dir incase it's missing.
        if cache_dir[-1] != '/':
            cache_dir += '/'

        self._cache_dir = cache_dir
        self._cache = []
        self._refresh_cache()

    def _refresh_cache(self):
        """Refresh the internal cache list."""

        self.data = []

        for f in os.listdir(self._cache_dir):
            self.data.append(ArchiveFile(f))

        self.data.sort()

    def add(self, filepath: str) -> bool:
        """Copy the file into cache.

        Parameters
        ----------
        filepath: str
            Path to a file to add to the cache.

        Raises
        ------
        FileNotFoundError
            filepath is not a valid file.

        Returns
        -------
        bool
            True if the file was copied into the cache or False if the filename
            format was wrong.
        """

        filename = os.path.basename(filepath)

        if self._file_regex.match(filename) is None:
            return False

        shutil.copyfile(filepath, self._cache_dir + filename)

        self.data.append(ArchiveFile(filepath))
        self.data.sort()

        return True

    def pop(self, path_dir: str) -> str:
        """Move the file with the oldest date in the filename to another dir.

        Parameters
        ----------
        path_dir : str
            Absolute path to a directory to add the old file.

        Returns
        -------
        str
            Absolute path to new file or an empty string if the cache is empty.
        """

        # add a '/' to end of dir_dir incase it's missing.
        if path_dir[-1] != '/':
            path_dir += '/'

        if len(self.data) == 0:
            return ""  # cache is empty

        new_file = path_dir + self.data[0].name
        shutil.copyfile(self.data[0].path, new_file)

        return new_file

    def clear(self):
        """Delete all files in the cache."""

        shutil.rmtree(self._cache_dir, ignore_errors=True)
        Path(self._cache_dir).mkdir(parents=True, exist_ok=True)
        self._refresh_cache()

    def json_str(self) -> str:
        """Makes a JSON str with the list of files in the cache.

        Returns
        -------
        str
            A JSON str with a list of the files in the cache.
        """

        return json.dumps(self._cache)

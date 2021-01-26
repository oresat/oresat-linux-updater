"""File Cache"""

import os
import shutil
import json
from pathlib import Path


class FileCache():
    """Used to store the update archive files sent to the linux updater."""

    def __init__(self, cache_dir: str):
        """
        Parameters
        ----------
        cache_dir: str
            The path to a directory for the cache.
        """

        # If the directory does not make it
        Path(cache_dir).mkdir(parents=True, exist_ok=True)

        # a / to end of cache_dir_dir incase it's missing.
        if cache_dir[-1] != '/':
            cache_dir += '/'

        self._cache_dir = cache_dir

    def __len__(self) -> int:
        """Gets the number of files in the cache.

        Returns
        -------
        int
            The number file in the cache.
        """

        return len(os.listdir(self._cache_dir))

    def add(self, file_dir: str):
        """Copy the file into cache.

        Parameters
        ----------
        file_dir: str
            Path to a file to add to the cache.

        Raises
        ------
        FileNotFoundError
        """

        filename = os.path.basename(file_dir)

        shutil.copyfile(file_dir, self._cache_dir + filename)

    def get(self, path_dir: str) -> str:
        """Copy the file from the cache to dir_dir.

        Parameters
        ----------
        path_dir : str
            Absolute path to a directory to add the old file.

        Returns
        -------
        str
            Path to new file.
        None
            No files in cache.
        """

        # add a '/' to end of dir_dir incase it's missing.
        if path_dir[-1] != '/':
            path_dir += '/'

        file_list = os.listdir(self._cache_dir)

        if file_list is None or len(file_list) <= 0:
            return None  # cache is empty

        archvice_filepath = self._cache_dir + file_list[0]
        new_file = path_dir + file_list[0]
        shutil.copyfile(archvice_filepath, new_file)

        return new_file

    def remove(self, filename: str):
        """Removes a sepecific file from the cache.

        Parameters
        ----------
        filepath : str
            Archive filename to delete from cache.

        Raises
        ------
        FileNotFoundError
        """

        os.remove(self._cache_dir + filename)

    def remove_all(self):
        """Delete all files in the cache."""

        shutil.rmtree(self._cache_dir, ignore_errors=True)
        Path(self._cache_dir).mkdir(parents=True, exist_ok=True)

    def json_str(self) -> str:
        """Makes a JSON str with the list of files in the cache.

        Returns
        -------
        str
            A JSON str with a list of the files in the cache.
        """

        return json.dumps(os.listdir(self._cache_dir).sort())

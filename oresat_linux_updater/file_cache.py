"""File Cache"""

import os
import shutil
from pathlib import Path


class FileCache():
    """
    Used to store the archvive files sent to the linux updater.

    Attributes
    ----------
    _cache_path: str
        The absolute path to the cache directory.
    _cache_len: int
        The number of files in the cache directory.
    """

    def __init__(self, cache_dir_path: str):
        """
        parameters
        ----------
        cache_dir_file : str
            The path to a directory for the cache.

        Raise
        -----
        AttributeError
            The cache_dir_path is empty
        """

        if cache_dir_path == "":
            raise AttributeError("No cache directory")

        # If the directory does not make it
        Path(cache_dir_path).mkdir(parents=True, exist_ok=True)

        # a / to end of cache_dir_path incase it's missing.
        if cache_dir_path[-1] != '/':
            cache_dir_path += '/'

        # Set attributes
        self._cache_path = cache_dir_path
        self._cache_len = len(os.listdir(self._cache_path))

    def __len__(self):
        """
        Gets the number of files in the cache.

        Returns
        -------
        int
            The number file in the cache.
        """

        return self._cache_len

    def add(self, file_path: str):
        """
        Add a file to the cache.
        correct format.

        Parameters
        ----------
        file_path : str
            Path to a file to add to the cache.

        Raise
        -----
        OSError
            File input error

        Returns
        -------
        bool
            True if file was added or False if file was not added
        """

        if not os.path.isfile(file_path):
            msg = file_path + " not found"
            raise OSError(msg)

        filename = os.path.basename(file_path)

        shutil.copyfile(file_path, self._cache_path + filename)
        self._cache_len = len(os.listdir(self._cache_path))

        return True

    def get(self, dir_path: str):
        """
        Copy the file from the cache to dir_path.

        Parameters
        ----------
        dir_path : str
            Absolute path to a directory to add the old file.

        Returns
        -------
        str
            Path to new file.
        """

        if not os.path.isdir(dir_path):
            msg = dir_path + " is not a vaild path"
            raise IOError(msg)

        # a / to end of dir_path incase it's missing.
        if dir_path[len(dir_path) - 1] != '/':
            dir_path += '/'

        if self._cache_len <= 0:
            return None  # cache is empty

        file_list = file_list = os.listdir(self._cache_path)

        if file_list:
            file_list.sort()
            archvice_filepath = self._cache_path + file_list[0]
        else:
            return None  # no files

        ret = shutil.copyfile(archvice_filepath, dir_path + file_list[0])
        return ret

    def remove(self, filename: str):
        """
        Gets the number of files in the cache.

        Parameters
        ----------
        filepath : str
            Archive filename to delete from cache.

        Returns
        -------
        bool
            True if the remove worked otherwise False on failure.
        """

        os.remove(self._cache_path + filename)
        return True

    def remove_all(self):
        """
        Delete all files in the cache.
        """

        shutil.rmtree(self._cache_path)
        Path(self._cache_path).mkdir(parents=True, exist_ok=True)
        return True

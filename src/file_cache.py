import os, shutil


class FileCache():
    """
    Used to store the archvive files sent to the linux updater.
    """

    #: The absolute path to the cache directory.
    _cache_path = ""

    #: The number of files in the cache directory.
    _cache_len = 0

    def __init__(self, cache_dir_path):
        # type: (str) -> ()
        """
        parameters
        ----------
        dir_file : str
            The absolute path to a directory for the cache.
        """

        # If the directory does not make it
        Path(cache_dir_path).mkdir(parents=True, exist_ok=True)

        # a / to end of cache_dir_path incase it's missing.
        if dir_path[len(cache_dir_path) - 1] != '/':
            cache_dir_path += '/'

        # Set attributes
        self._cache_path = cache_dir_path
        self._cache_len = len(os.listdir(self._cache_path))


    def add(self, file_path):
        # type: (str) -> bool
        """
        Add a file to the cache.
        correct format.

        Parameters
        ----------
        file_path : str
            Absolute path to a file to add to the cache.

        Raises
        ------
        ValueError
            dir_path was empty or not a absolute path.

        Returns
        -------
        bool
            True if file was added or False if file was not added
        """

        # make sure input was valid
        if not file_path:
            raise ValueError("Input was empty.")
        if(file_path[0] != '/'):
            raise ValueError("Input was not an absolute path.")

        ret = shutil.copyfile(file_path, self._cache_path)
        self._cache_len = len(os.listdir(self._cache_path))

        return True


    def get(self, dir_path):
        # type: (str) -> str
        """
        Copy the file from the cache to dir_path.

        Parameters
        ----------
        dir_path : str
            Absolute path to a directory to add the old file.

        Raises
        ------
        ValueError
            dir_path was empty or not a absolute path.

        Returns
        -------
        str
            Path to new file.
        """

        # make sure input is valid
        if not dir_path:
            raise ValueError("Input was empty.")
        elif dir_path[0] != '/':
            raise ValueError("Input was not an absolute path.")

        # a / to end of dir_path incase it's missing.
        if dir_path[len(dir_path) - 1] != '/':
            dir_path += '/'

        if self._cache_len <= 0:
            return None # cache is empty

        file_list =file_list = os.listdir(self._cache_path) os.listdir(self._cache_path)

        if file_list:
            file_list.sort()
            archvice_filepath = self._cache_path + file_list[0]
        else:
            return None # no files

        ret = shutil.copyfile(archvice_filepath, dir_path + file_list[0])
        return ret


    def len(self):
        # type: () -> int
        """
        Gets the number of files in the cache.

        Returns
        -------
        int
            The number file in the cache.
        """

        return self._cache_len


    def remove(self, filename):
        # type: (str) -> bool
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

        try:
            os.remove(self._cache_path + filename)
        except:
            return False

        return True


    def remove_all(self):
        """
        Delete all files in the cache.
        """

        shutil.rmtree(cache_dir_path)
        Path(cache_dir_path).mkdir(parents=True, exist_ok=True)

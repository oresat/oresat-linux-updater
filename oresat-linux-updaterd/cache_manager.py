import os, re, shutil


class ArchiveFileCache():

    def _init_(self, cache_dir_path):
        Path(cache_dir_path).mkdir(parents=True, exist_ok=True)
        self._cache_path = cache_dir_path
        self._cache_len = len(os.listdir(self._cache_path))


    def add(self, file_path):
    """Calculates topocentric coordinates for a satellite at a datetime.

    Parameters
    ---------
    file_path : str
        Absolute path to a file to add to teh cache.

    Returns
    -------
    Boolean
        - True 
    """
        """ copies file into cache_dir_path """
        if(file_path[0] != '/'):
            raise ValueError("Input need to be an absolute path.")

        # check for valid update file
        if not re.match(r"(update-\d\d\d\d-\d\d-\d\d-\d\d-\d\d\.tar\.gz)", file_path:
            return False

        ret = shutil.copyfile(file_path, self._cache_path)
        self._cache_len = len(os.listdir(self._cache_path))
        return True


    def get(self, dist_path):
        # get the oldest archive file
        if(dist_path[0] != '/'):
            raise ValueError("Input need to be an absolute path.")

        if self._cache_len <= 0:
            return False # cache is empty

        file_list = os.listdir(self._cache_path)

        if file_list:
            file_list.sort()
            archvice_filepath = self._cache_path + file_list[0]
        else:
            return False # no files

        ret = shutil.copyfile(archvice_filepath, dist_path)
        return True


    def len(self):
        # number of items in cache
        return self._cache_len


    def remove(self, filename):
        os.remove(self._cache_path + filename)


    def remove_all(self):
        # delete all file in cache
        shutil.rmtree(cache_dir_path)
        Path(cache_dir_path).mkdir(parents=True, exist_ok=True)

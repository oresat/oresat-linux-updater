"""tests for the FileCache class"""

import os
import shutil
import pytest
from oresat_linux_updater.file_cache import FileCache
from .common import TEST_WORK_DIR, TEST_CACHE_DIR, VALID_INSTALL, \
        VALID_INSTALL_PATH, VALID_REMOVE, VALID_REMOVE_PATH


@pytest.fixture
def file_cache():
    """make the file_cache object"""
    shutil.rmtree(TEST_CACHE_DIR, ignore_errors=True)
    shutil.rmtree(TEST_WORK_DIR, ignore_errors=True)
    os.mkdir(TEST_WORK_DIR)
    return FileCache(TEST_CACHE_DIR)


def test_add_remove(file_cache):
    """test add files to the file cache and removing them"""

    assert len(file_cache) == 0

    # invalid filepath
    with pytest.raises(FileNotFoundError):
        file_cache.add("kslajdlkajd")

    assert len(file_cache) == 0

    # test with empty cache
    file_cache.add(VALID_INSTALL_PATH)

    assert len(file_cache) == 1

    # test with non empty cache
    file_cache.add(VALID_REMOVE_PATH)

    assert len(file_cache) == 2

    # remove file
    file_cache.remove(VALID_REMOVE)

    assert len(file_cache) == 1

    # try remove no existing file
    with pytest.raises(FileNotFoundError):
        file_cache.remove(VALID_REMOVE)

    assert len(file_cache) == 1

    # remove file
    file_cache.remove(VALID_INSTALL)

    assert len(file_cache) == 0


def test_get(file_cache):
    """test geting a file from file cache"""

    assert file_cache.get(TEST_WORK_DIR) is None

    file_cache.add(VALID_INSTALL_PATH)

    with pytest.raises(FileNotFoundError):
        file_cache.get("daslkdaks")

    assert file_cache.get(TEST_WORK_DIR) is not None

    file_cache.remove(VALID_INSTALL)

    assert len(file_cache) == 0


def test_remove_all(file_cache):
    """test removing all files from file cache"""

    assert len(file_cache) == 0

    file_cache.remove_all()

    assert len(file_cache) == 0

    file_cache.add(VALID_INSTALL_PATH)
    file_cache.add(VALID_REMOVE_PATH)

    assert len(file_cache) == 2

    file_cache.remove_all()

    assert len(file_cache) == 0

import pytest
from oresat_updaterd.file_cache import FileCache

FILE_CACHE = None
cache_dir_path = "./testcache/"
filename = "test_file"
filename2 = "test_file2"


def test_file_cache():
    """test FileCache constructor"""

    global FILE_CACHE
    FILE_CACHE = FileCache(cache_dir_path)

    assert True


def test_len_0():
    """test FileCache len"""

    assert len(FILE_CACHE) == 0


def test_add_no_file():
    """test adding a file to file cache"""

    # test with non existant file
    with pytest.raises(Exception):
        assert FILE_CACHE.add("aksdlaksdl")


def test_add():
    # make a files for testing
    with open(filename, "w") as f:
        f.write("Hello, World!")
    with open(filename2, "w") as f:
        f.write("Hello, World 2!")

    # test with empty cache
    ret = FILE_CACHE.add(filename)
    assert ret

    # test with non empty cache
    ret = FILE_CACHE.add(filename2)
    assert ret

    # might aswell
    assert len(FILE_CACHE) == 2

    assert True


def test_get():
    """test geting a file from file cache"""
    assert FILE_CACHE.remove(filename, )


def test_remove():
    """test removing a file from file cache"""

    with pytest.raises(Exception):
        assert FILE_CACHE.remove("dkalskdaldka") is False
        assert FILE_CACHE.remove(filename)


def test_remove_all():
    """test removing all files from file cache"""

    assert FILE_CACHE.remove_all()

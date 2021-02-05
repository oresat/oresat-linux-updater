"""tests for the status archive functions"""

from os import remove
from os.path import isfile
from oresat_linux_updater.status_archive import make_status_archive
from .common import TEST_FILE_DIR


def test_make_status_file():
    status_file = make_status_archive(TEST_FILE_DIR, True)
    assert isfile(status_file)
    remove(status_file)

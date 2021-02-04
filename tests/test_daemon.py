"""tests for the UpdaterDaemon class"""

import shutil
import time
import pytest
from os import remove
from os.path import isfile
from .common import TEST_WORK_DIR, TEST_CACHE_DIR, LOGGER, TEST_UPDATE0, \
        TEST_UPDATE1, TEST_UPDATE2, TEST_UPDATE3, TEST_UPDATE9, \
        clear_test_cache_dir, clear_test_work_dir
from oresat_linux_updater.daemon import Daemon, Result


@pytest.fixture
def daemon():
    """make the file_cache object"""
    clear_test_cache_dir()
    clear_test_work_dir()
    return Daemon(TEST_WORK_DIR, TEST_CACHE_DIR, LOGGER)


def test_loop(daemon):

    daemon.start()
    time.sleep(0.05)
    daemon.quit()


def test_add_update(daemon):

    assert daemon.AvailableUpdateFiles == 0

    assert daemon.AddUpdateFile(TEST_UPDATE1)

    assert daemon.AvailableUpdateFiles == 1

    assert daemon.AddUpdateFile(TEST_UPDATE2)

    assert daemon.AvailableUpdateFiles == 2

    assert not daemon.AddUpdateFile(TEST_UPDATE9)

    assert daemon.AvailableUpdateFiles == 2

    assert not daemon.AddUpdateFile("Invalid_file")

    assert daemon.AvailableUpdateFiles == 2


def test_update(daemon):

    # test valid updates and correct ordering
    # should fails on the 3rd update due to missing dependencies
    # should run in order 0 -> 1 -> 2
    # when 2 fails cache should be cleared
    assert daemon.AvailableUpdateFiles == 0
    daemon.AddUpdateFile(TEST_UPDATE0)
    daemon.AddUpdateFile(TEST_UPDATE1)
    daemon.AddUpdateFile(TEST_UPDATE2)
    daemon.AddUpdateFile(TEST_UPDATE3)
    assert daemon.AvailableUpdateFiles == 4
    assert daemon._update() is Result.SUCCESS
    assert daemon.AvailableUpdateFiles == 3
    assert daemon._update() is Result.SUCCESS
    assert daemon.AvailableUpdateFiles == 2
    assert daemon._update() is Result.FAILED_CRIT
    assert daemon.AvailableUpdateFiles == 0

    daemon.AddUpdateFile(TEST_UPDATE3)
    assert daemon._update() is Result.FAILED_NON_CRIT
    assert daemon.AvailableUpdateFiles == 0


def test_make_status_file(daemon):
    status_file = daemon._make_status_file()
    assert isfile(status_file)
    remove(status_file)

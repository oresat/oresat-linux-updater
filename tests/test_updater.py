"""tests for the Updater class"""

import time
import pytest
from oresat_linux_updater.updater import Updater, Result
from .common import TEST_WORK_DIR, TEST_CACHE_DIR, LOGGER, TEST_UPDATE0, \
        TEST_UPDATE1, TEST_UPDATE2, TEST_UPDATE3, TEST_UPDATE9, \
        clear_test_cache_dir, clear_test_work_dir


@pytest.fixture
def updater():
    """make the file_cache object"""
    clear_test_cache_dir()
    clear_test_work_dir()
    return Updater(TEST_WORK_DIR, TEST_CACHE_DIR, LOGGER)


def test_loop(updater):

    updater.start()
    time.sleep(0.05)
    updater.quit()


def test_add_update(updater):

    assert updater.AvailableUpdateArchives == 0

    assert updater.AddUpdateArchive(TEST_UPDATE1)

    assert updater.AvailableUpdateArchives == 1

    assert updater.AddUpdateArchive(TEST_UPDATE2)

    assert updater.AvailableUpdateArchives == 2

    assert not updater.AddUpdateArchive(TEST_UPDATE9)

    assert updater.AvailableUpdateArchives == 2

    assert not updater.AddUpdateArchive("Invalid_file")

    assert updater.AvailableUpdateArchives == 2


def test_update(updater):

    # test valid updates and correct ordering
    # should fails on the 3rd update due to missing dependencies
    # should run in order 0 -> 1 -> 2
    # when 2 fails cache should be cleared
    assert updater.AvailableUpdateArchives == 0
    updater.AddUpdateArchive(TEST_UPDATE0)
    updater.AddUpdateArchive(TEST_UPDATE1)
    updater.AddUpdateArchive(TEST_UPDATE2)
    updater.AddUpdateArchive(TEST_UPDATE3)
    assert updater.AvailableUpdateArchives == 4
    assert updater._update() is Result.SUCCESS
    assert updater.AvailableUpdateArchives == 3
    assert updater._update() is Result.SUCCESS
    assert updater.AvailableUpdateArchives == 2
    assert updater._update() is Result.FAILED_CRIT
    assert updater.AvailableUpdateArchives == 0

    updater.AddUpdateArchive(TEST_UPDATE3)
    assert updater._update() is Result.FAILED_NON_CRIT
    assert updater.AvailableUpdateArchives == 0

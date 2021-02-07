"""tests for the Updater class"""

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


def test_default_update_properties(updater):
    # test all property are back to default
    assert updater.is_updating is False
    assert updater.update_archive == ""
    assert updater.total_instructions == 0
    assert updater.instruction_index == 0
    assert updater.instruction_command == ""


def test_add_update(updater):

    assert updater.available_update_archives == 0

    assert updater.add_update_archive(TEST_UPDATE1)
    assert updater.available_update_archives == 1

    assert updater.add_update_archive(TEST_UPDATE2)
    assert updater.available_update_archives == 2

    assert not updater.add_update_archive(TEST_UPDATE9)
    assert updater.available_update_archives == 2

    assert not updater.add_update_archive("Invalid_file")
    assert updater.available_update_archives == 2

    test_default_update_properties(updater)


def test_update(updater):

    # test valid updates and correct ordering
    # should fails on the 3rd update due to missing dependencies
    # should run in order 0 -> 1 -> 2
    # when 2 fails cache should be cleared
    assert updater.available_update_archives == 0
    updater.add_update_archive(TEST_UPDATE0)
    updater.add_update_archive(TEST_UPDATE1)
    updater.add_update_archive(TEST_UPDATE2)
    updater.add_update_archive(TEST_UPDATE3)
    assert updater.available_update_archives == 4

    assert updater.update() == Result.SUCCESS.value
    assert updater.available_update_archives == 3
    test_default_update_properties(updater)

    assert updater.update() == Result.SUCCESS.value
    assert updater.available_update_archives == 2
    test_default_update_properties(updater)

    assert updater.update() == Result.FAILED_CRIT.value
    assert updater.available_update_archives == 0
    test_default_update_properties(updater)

    # test bad update
    updater.add_update_archive(TEST_UPDATE3)
    assert updater.available_update_archives == 1
    assert updater.update() == Result.FAILED_NON_CRIT.value
    assert updater.available_update_archives == 0
    test_default_update_properties(updater)

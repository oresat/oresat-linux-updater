"""tests for the UpdaterDaemon class"""

import time
import pytest
from .common import TEST_WORK_DIR, TEST_CACHE_DIR, LOGGER
from oresat_linux_updater.updater_daemon import UpdaterDaemon


@pytest.fixture
def updater_daemon():
    """make the file_cache object"""
    return UpdaterDaemon(TEST_WORK_DIR, TEST_CACHE_DIR, LOGGER)


def test_loop(updater_daemon):

    updater_daemon.start()
    time.sleep(0.05)
    updater_daemon.quit()

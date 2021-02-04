"""common global variables for all tests"""

import sys
import logging
from shutil import rmtree
from os.path import dirname
from pathlib import Path

# test logger
LOGGER = logging.getLogger('olu unit test')
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(logging.StreamHandler(sys.stderr))

# test directories
TEST_CACHE_DIR = "test_cache_dir/"
TEST_WORK_DIR = "test_work_dir/"
TEST_FILE_DIR = dirname(__file__) + "/test_files/"

# test deb files
TEST_DEB_PKG1_NAME = "test-package1"
TEST_DEB_PKG2_NAME = "test-package2"
TEST_BASH_SCRIPT = TEST_FILE_DIR + "test-script.sh"
TEST_DEB_PKG1 = TEST_FILE_DIR + "test-package1_0.1.0-0_all.deb"
TEST_DEB_PKG2 = TEST_FILE_DIR + "test-package2_0.1.0-0_all.deb"

# test instructions files
TEST_INST_FILE1 = TEST_FILE_DIR + "instructions1.txt"
TEST_INST_FILE2 = TEST_FILE_DIR + "instructions2.txt"
TEST_INST_FILE3 = TEST_FILE_DIR + "instructions3.txt"
TEST_INST_FILE4 = TEST_FILE_DIR + "instructions4.txt"
TEST_INST_FILE5 = TEST_FILE_DIR + "instructions5.txt"

# test update archives
TEST_UPDATE0 = TEST_FILE_DIR + "test_update_1611940000.tar.xz"
TEST_UPDATE1 = TEST_FILE_DIR + "test_update_1611941111.tar.xz"
TEST_UPDATE2 = TEST_FILE_DIR + "test_update_1611942222.tar.xz"
TEST_UPDATE3 = TEST_FILE_DIR + "test_update_1611943333.tar.xz"
TEST_UPDATE4 = TEST_FILE_DIR + "test_update_1611944444.tar.xz"
TEST_UPDATE5 = TEST_FILE_DIR + "test_update_1611945555.tar.xz"
TEST_UPDATE6 = TEST_FILE_DIR + "test_update_1611946666.tar.xz"
TEST_UPDATE7 = TEST_FILE_DIR + "test_update_1611947777.tar.xz"
TEST_UPDATE8 = TEST_FILE_DIR + "test_update_1611948888.tar.xz"
TEST_UPDATE9 = TEST_FILE_DIR + "test_update.tar.xz"


def clear_test_work_dir():
    """Clear the test work directory."""
    rmtree(TEST_WORK_DIR, ignore_errors=True)
    Path(TEST_WORK_DIR).mkdir(parents=True, exist_ok=True)


def clear_test_cache_dir():
    """Clear the test cache directory."""
    rmtree(TEST_CACHE_DIR, ignore_errors=True)
    Path(TEST_CACHE_DIR).mkdir(parents=True, exist_ok=True)

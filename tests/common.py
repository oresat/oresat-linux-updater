"""common global variables for all tests"""

import sys
import logging

# test logger
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
LOGGER = logging.getLogger('olu unit test')
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(logging.StreamHandler(sys.stderr))

# test directories
TEST_CACHE_DIR = "./test_cache_dir/"
TEST_WORK_DIR = "./test_work_dir/"
TEST_FILE_DIR = "./test_files/"

# test deb files
TEST_DEB_PKG1 = "test-package1_0.1.0-0_all.deb"
TEST_DEB_PKG1_PATH = TEST_FILE_DIR + TEST_DEB_PKG1
TEST_DEB_PKG2 = "test-package2_0.1.0-0_all.deb"
TEST_DEB_PKG2_PATH = TEST_FILE_DIR + TEST_DEB_PKG2

# test update archives
VALID_INSTALL = "test_update_2021-01-01-00-00-00.tar.xz"
VALID_INSTALL_PATH = TEST_FILE_DIR + VALID_INSTALL
VALID_REMOVE = "test_update_2021-01-01-01-01-01.tar.xz"
VALID_REMOVE_PATH = TEST_FILE_DIR + VALID_REMOVE
INVALID_INSTALL = "test_update_2021-01-01-02-02-02.tar.xz"
INVALID_INSTALL_PATH = TEST_FILE_DIR + INVALID_INSTALL
MISSING_INSTRUCTIONS = "test_update_2021-01-01-03-03-03.tar.xz"
MISSING_INSTRUCTIONS_PATH = TEST_FILE_DIR + MISSING_INSTRUCTIONS
MISSING_DEB = "test_update_2021-01-01-04-04-04.tar.xz"
MISSING_DEB_PATH = TEST_FILE_DIR + MISSING_DEB
MISSING_SCRIPT = "test_update_2021-01-01-05-05-05.tar.xz"
MISSING_SCRIPT_PATH = TEST_FILE_DIR + MISSING_SCRIPT
INVALID_TAR_XZ = "test_update_2021-01-01-06-06-06.tar.xz"
INVALID_TAR_XZ_PATH = TEST_FILE_DIR + INVALID_TAR_XZ
INVALID_JSON = "test_update_2021-01-01-07-07-07.tar.xz"
INVALID_JSON_PATH = TEST_FILE_DIR + INVALID_JSON
INVALID_COMMAND = "test_update_2021-01-01-08-08-08.tar.xz"
INVALID_COMMAND_PATH = TEST_FILE_DIR + INVALID_COMMAND
INVALID_REMOVE = "test_update_2021-01-01-09-09-09.tar.xz"
INVALID_REMOVE_PATH = TEST_FILE_DIR + INVALID_REMOVE

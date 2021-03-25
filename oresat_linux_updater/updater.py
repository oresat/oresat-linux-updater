"""Linux updater daemon"""

import json
from logging import Logger
from os import listdir
from os.path import abspath, basename
from shutil import copyfile, move, rmtree
from pathlib import Path
from enum import IntEnum, auto
from threading import Lock
from oresat_linux_updater.olm_file import OLMFile
from oresat_linux_updater.update_archive import extract_update_archive, \
        is_update_archive, UpdateArchiveError, InstructionError


class UpdaterError(Exception):
    """An error occurred in Updater class."""


class Result(IntEnum):
    """The integer value Updater's update() will return"""

    NOTHING = 0
    """Nothing for the updater to do. The cache was empty or there was nothing
    to resume.
    """

    SUCCESS = auto()
    """The update successfully install."""

    FAILED_NON_CRIT = auto()
    """The update failed during the inital non critical section. Either the was
    an error using the file cache, when opening tarfile, or reading the
    instructions file.
    """

    FAILED_CRIT = auto()
    """The update failed during the critical section. The updater fail while
    following the instructions.
    """


class Updater():
    """The OreSat Linux updater. Allows OreSat Linux boards to be update thru
    update archives.

    While this could be replaced with a couple of functions. Having a object
    with properties, allow for easy to get status info while updating. All
    properties are readonly.

    All functions and properties are thread safe.

    """

    def __init__(self, work_dir: str, cache_dir: str, logger: Logger):
        """
        Parameters
        ----------
        work_dir: str
            Directory to use a the working dir. Should be a abslute path.
        cache_dir: str
            Directory to store update archives in. Should be a abslute path.
        logger: logging.Logger
            The logger object to use.
        """

        self._log = logger

        # make update_archives for cache dir
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        self._cache_dir = abspath(cache_dir) + "/"
        self._log.debug("cache dir " + self._cache_dir)

        # make update_archives for work dir
        Path(work_dir).mkdir(parents=True, exist_ok=True)
        self._work_dir = abspath(work_dir) + "/"
        self._log.debug("work dir " + self._work_dir)

        # mutex and things protected by lock
        self._lock = Lock()
        self._is_updating = False
        self._update_archive = ""
        self._total_instructions = 0
        self._current_instruction_index = 0
        self._current_command = ""
        self._cache = listdir(self._cache_dir)
        self._cache.sort()

    def clear_cache_dir(self):
        """Clears the working directory."""

        self._log.info("clearing update archive cache directory")
        if len(listdir(self._work_dir)) != 0:
            rmtree(self._work_dir, ignore_errors=True)
            Path(self._work_dir).mkdir(parents=True, exist_ok=True)
            self._cache = listdir(self._cache_dir)

    def add_update_archive(self, update_archive: str) -> bool:
        """Copies update archive into the update archive cache.

        Parameters
        ----------
        update_archive: str
            The absolute path to update archive for the updater to copy.

        Returns
        -------
        bool
            True if a file was added or False on failure.
        """

        ret = True
        filename = basename(update_archive)

        try:
            OLMFile(load=update_archive)
            copyfile(update_archive, self._cache_dir + filename)
            self._cache.append(filename)
            self._cache.sort()
            self._log.info(filename + " was added to cache")
        except Exception:
            self._log.error(filename + " is a invalid filename")
            ret = False

        return ret

    def update(self) -> int:
        """Run a update.

        If there are file aleady in the working directory, it will try to find
        and resume the update, otherwise it will get the oldest archive from
        the update archive cache and run it.

        If the update fails, the cache will be cleared, as it is asume all
        newer updates require the failed updated to be run successfully first.

        Raises
        ------
        UpdaterError
            If called when already updating.

        Returns
        -------
        int
            A :class:`Result` value.
        """

        ret = Result.SUCCESS
        self._lock.acquire()

        if self._is_updating:
            self._lock.release()
            raise UpdaterError("can't start an new update while updating")

        self._update_archive = ""
        self._is_updating = True
        self._lock.release()

        # something in working dir, see if it an update to resume
        file_list = listdir(self._work_dir)
        if len(file_list) != 0:
            self._log.info("files found in working dir")

            # find update archive in work directory
            for fname in file_list:
                if is_update_archive(fname):
                    self._update_archive = self._work_dir + fname
                    self._log.info("resuming update with " + fname)
                    break

            if self._update_archive == "":  # Nothing to resume
                self._log.info("nothing to resume")
                self._log.info("clearing working directory")
                rmtree(self._work_dir, ignore_errors=True)
                Path(self._work_dir).mkdir(parents=True, exist_ok=True)

        # if not resuming, get new update archive from cache
        if self._update_archive == "" and len(self._cache) != 0:
            self._update_archive = \
                move(self._cache_dir + self._cache.pop(0), self._work_dir)
            msg = "got {} from cache".format(basename(self._update_archive))
            self._log.info(msg)

        if self._update_archive == "":  # nothing to do
            ret = Result.NOTHING

        # if there is a update archive to use, open it
        if ret == Result.SUCCESS:
            self._update_archive = basename(self._update_archive)
            self._log.info("opening " + self._update_archive)
            try:
                inst_list = extract_update_archive(
                        self._work_dir + self._update_archive,
                        self._work_dir)
                self._log.debug(self._update_archive + " successfully opened")
            except (UpdateArchiveError, InstructionError, FileNotFoundError) \
                    as exc:
                self._log.critical(exc)
                ret = Result.FAILED_NON_CRIT

        # if update archive opened successfully, run the update
        if ret == Result.SUCCESS:
            self._log.info("running update")
            """
            No turn back point, the update is starting!!!
            If anything fails/errors the board's software could break.
            All errors are log at critical level.
            """
            try:
                self._total_instructions = len(inst_list)
                for i in range(self._total_instructions):
                    self._current_instruction_index = i
                    self._current_command = inst_list[i].bash_command
                    inst_list[i].run(self._log)
                self._log.debug(self._update_archive + " successfully ran")
            except (UpdateArchiveError, InstructionError, FileNotFoundError) \
                    as exc:
                self._log.critical(exc)
                ret = Result.FAILED_CRIT

        # if update failed
        if ret in [Result.FAILED_NON_CRIT, Result.FAILED_CRIT]:
            self._log.info("clearing file cache due to failed update")

            files = ""
            for i in self._cache:
                files += basename(i) + " "
            self._log.info("deleted " + files)

            rmtree(self._cache_dir, ignore_errors=True)
            Path(self._cache_dir).mkdir(parents=True, exist_ok=True)
            self._lock.acquire()
            self._cache = []
            self._lock.release()

        self._log.info("update {} result {}".format(self._update_archive, ret))
        self._log.debug("clearing working directory")
        rmtree(self._work_dir, ignore_errors=True)
        Path(self._work_dir).mkdir(parents=True, exist_ok=True)
        self._total_instructions = 0
        self._current_instruction_index = 0
        self._current_command = ""

        self._lock.acquire()
        self._update_archive = ""
        self._is_updating = False
        self._lock.release()
        return ret.value

    @property
    def available_update_archives(self) -> int:
        """int: The number of update archives in cache. Readonly."""

        return len(self._cache)

    @property
    def list_updates(self) -> str:
        """str: Get a JSON list of filename in cache. Readonly."""

        return json.dumps(self._cache)

    @property
    def is_updating(self) -> bool:
        """bool: Flag if the updater is updating or not."""

        return self._is_updating

    @property
    def update_archive(self) -> str:
        """str: Current update archive while updating. Will be a empty
        str if the daemon is not currently updating. Readonly.
        """

        return self._update_archive

    @property
    def total_instructions(self) -> int:
        """int: The total number of instructions in the update running. Will be
        0 if the not currently updating. Readonly.
        """

        return self._total_instructions

    @property
    def instruction_index(self) -> int:
        """int: The index of the instruction currently running. Will be 0 if
        the not currently updating. Readonly.
        """

        return self._current_instruction_index

    @property
    def instruction_command(self) -> str:
        """str: The current bash command being running. Will be an empty
        str if the not currently updating. Readonly.
        """

        return self._current_command

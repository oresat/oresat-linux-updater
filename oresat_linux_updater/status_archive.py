"""File for creating status archive or existing files from staus archives."""

import json
import tarfile
from os import listdir, remove
from os.path import basename, isfile, isdir
from oresat_linux_updater.olm_file import OLMFile

OLU_STATUS_KEYWORD = "olu-status"
DPKG_STATUS_KEYWORD = "dpkg-status"
DPKG_STATUS_FILE = "/var/lib/dpkg/status"


def read_olu_status_file(name: str) -> str:
    """Read the contents of the olu status file in the status archive

    Parameters
    ----------
    name: str
        The olu status tar file.

    Raises
    ------
    FileNotFoundError

    Returns
    -------
    str
        The contents of the olu file.
    """

    status_file = ""
    tar = tarfile.open(name, "r")

    for i in tar.getmembers():
        olm_file = OLMFile(load=i.name)
        if olm_file.keyword == OLU_STATUS_KEYWORD:
            status_file = olm_file.name
            fptr = tar.extractfile(status_file)
            content = fptr.read()
            content = content.decode("utf-8")
            tar.close()
            break

    if status_file == "":
        tar.close()
        raise FileNotFoundError("missing olu-status file in {}".format(name))

    return content


def read_dpkg_status_file(name: str):
    """Read the contents of the dpkg status file in the status archive if it
    exit.

    Parameters
    ----------
    name: str
        The olu status tar file.

    Raises
    ------
    FileNotFoundError

    Returns
    -------
    str
        The contents of the dpkg file.
    """

    status_file = ""
    tar = tarfile.open(name, "r")

    for i in tar.getmembers():
        olm_file = OLMFile(load=i.name)
        if olm_file.keyword == DPKG_STATUS_KEYWORD:
            status_file = olm_file.name
            fptr = tar.extractfile(status_file)
            content = fptr.read()
            content = content.decode("utf-8")
            tar.close()
            break

    if status_file == "":
        tar.close()
        raise FileNotFoundError("missing dpkg-status file in {}".format(name))

    return content


def make_status_archive(update_cache_dir: str, dpkg_status=False) -> str:
    """Make status tar file with a copy of the dpkg status file and a file
    with the list of updates in cache.

    Parameters
    ----------
    update_cache_dir: str
        Path to the update archive cache.
    dpkg_status: bool
        Include the dpkg status file to update archive.

    Raises
    ------
    FileNotFoundError

    Returns
    -------
    str
        Path to new status file or empty string on failure.
    """

    # make sure all files and dirs exist
    if not isdir(update_cache_dir):
        raise FileNotFoundError("{} is missing".format(update_cache_dir))
    if dpkg_status and not isfile(DPKG_STATUS_FILE):
        raise FileNotFoundError("{} is missing".format(DPKG_STATUS_FILE))

    # make the filenames
    olu_file = "/tmp/" + OLMFile(keyword=OLU_STATUS_KEYWORD).name
    olu_tar = "/tmp/" + OLMFile(keyword=OLU_STATUS_KEYWORD, ext=".tar.xz").name
    if dpkg_status:
        dpkg_file = OLMFile(keyword=DPKG_STATUS_KEYWORD).name

    with open(olu_file, "w") as fptr:
        fptr.write(json.dumps(listdir(update_cache_dir)))

    with tarfile.open(olu_tar, "w:xz") as tfptr:
        tfptr.add(olu_file, arcname=basename(olu_file))
        if dpkg_status:
            tfptr.add(DPKG_STATUS_FILE, arcname=basename(dpkg_file))

    remove(olu_file)
    return olu_tar

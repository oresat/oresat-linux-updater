""" OreSat Linux Updater Setup.py """

from setuptools import setup
import oresat_linux_updater as olu

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name=olu.APP_NAME,
    version=olu.APP_VERSION,
    author=olu.APP_AUTHOR,
    license=olu.APP_LICENSE,
    description=olu.APP_DESCRIPTION,
    long_description=long_description,
    author_email="rmedick@pdx.edu",
    maintainer="Ryan Medick",
    maintainer_email="rmedick@pdx.edu",
    url="https://github.com/oresat/oresat-linux-updater",
    packages=['oresat-linux-updater'],
    install_requires=[
        "apt",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)

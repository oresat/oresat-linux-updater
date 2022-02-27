'''CLI for making update archives.'''

import sys
from argparse import ArgumentParser
from os.path import isfile, basename
from shutil import copyfile
from pathlib import Path
from update_maker.update_maker import UpdateMaker


OLU_DIR = str(Path.home()) + '/.oresat_linux_updater/'
ROOT_DIR = OLU_DIR + 'root/'
DOWNLOAD_DIR = ROOT_DIR + 'var/cache/apt/archives/'
UPDATE_CACHE_DIR = OLU_DIR + 'update_cache/'
STATUS_CACHE_DIR = OLU_DIR + 'status_cache/'


def usage():
    '''Print usage'''
    print('''
    cli commands:
        add-pkg:    add deb package(s)
        remove-pkg: remove deb package(s)
        add-bash:   add bash script(s)
        add-files:  add support file(s)
        status:     print status
        make:       make the update archive file and quit
        quit:       quit the cli
    ''')


def creating_folders():
    # make sure all dir exist   
    Path(OLU_DIR).mkdir(parents=True, exist_ok=True)
    Path(ROOT_DIR).mkdir(parents=True, exist_ok=True)
    Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(UPDATE_CACHE_DIR).mkdir(parents=True, exist_ok=True)
    Path(STATUS_CACHE_DIR).mkdir(parents=True, exist_ok=True)


def add_olu_cache(add: str):
    # add olu-status tar files to the olu-status cache
    if add is not None:
        if isfile(add):
            copyfile(add, STATUS_CACHE_DIR + basename(add))
        else:
            msg = '{} is not a valid olu-status tar file'.format(add)
            raise FileNotFoundError(msg)


def reinstall_input(packages: list, not_installed_yet_list: list, not_removed_yet_list: list): 

    reinstall_not_installed = []
    reinstall_not_removed = []

    for pkg in packages:
        if pkg in not_removed_yet_list:
            command = input('-> Would you like to reinstall {}? [Y/n] '.format(pkg))
            if command == 'Y' or command == 'y' or command == 'yes':
                reinstall_not_removed.append(pkg)
        elif pkg in not_installed_yet_list:
            command = input('-> Would you like to reinstall {}? [Y/n] '.format(pkg))
            if command == 'Y' or command == 'y' or command == 'yes':
                reinstall_not_installed.append(pkg)

    return [reinstall_not_installed, reinstall_not_removed]


def main():
    parser = ArgumentParser(prog='python3 -m update_maker')
    parser.add_argument('board', metavar='<board>', default=None, nargs='?',
                        help='define the board used')
    parser.add_argument('-a', '--add',
                        help='add olu-status tar files to the olu-status cache')
    args = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    creating_folders()
    add_olu_cache(args.add)

    # check if board parameter exists
    if args.board is not None:
        maker = UpdateMaker(args.board)

        while True:
            command = input('-> ').split(' ')

            try:
                if command[0] == 'status':
                    maker.status()
                elif command[0] == 'help':
                    usage()
                elif command[0] == 'add-pkg':
                    reinstall_not_installed, reinstall_not_removed = reinstall_input(
                        command[1:],
                        maker.not_installed_yet,
                        maker.not_removed_yet)
                    maker.add_packages(command[1:], reinstall_not_installed, reinstall_not_removed)
                elif command[0] == 'remove-pkg':
                    maker.remove_packages(command[1:])
                elif command[0] == 'purge-pkg':
                    maker.purge_packages(command[1:])
                elif command[0] == 'add-bash':
                    maker.add_bash_scripts(command[1:])
                elif command[0] == 'add-files':
                    maker.add_support_files(command[1:])
                elif command[0] == 'make':
                    maker.make_update_archive()
                    break
                elif command[0] == 'quit':
                    break
                else:
                    print('not valid command')
            except Exception as exc:
                print(exc)

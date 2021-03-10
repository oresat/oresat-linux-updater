"""CLI for making update archives."""

import sys
from argparse import ArgumentParser
from update_maker.update_maker import UpdateMaker


def usage():
    """Print usage"""
    print("""
    python3 make_update_pacakge.py <board> <-a filepath>

    options and arguments:
        -a/--a:     add olu-status tar files to the olu-status cache

    cli commands:
        add-pkg:    add deb package(s)
        remove-pkg: remove deb package(s)
        add-bash:   add bash script(s)
        add-files:  add support file(s)
        status:     print status
        make:       make the update archive file and quit
        quit:       quit the cli
    """)


def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    parser = ArgumentParser()
    parser.add_argument("board", metavar="<board>", default=None, nargs='?',
                        help="define the board used")
    parser.add_argument("-a", "--add",
                        help="add olu-status tar files to the olu-status cache")
    args = parser.parse_args()

    maker = UpdateMaker(args.board, args.add)

    while True:
        command = input("-> ").split(" ")

        try:
            if command[0] == "status":
                maker.status()
            elif command[0] == "help":
                usage()
            elif command[0] == "add-pkg":
                maker.add_packages(command[1:])
            elif command[0] == "remove-pkg":
                maker.remove_packages(command[1:])
            elif command[0] == "purge-pkg":
                maker.purge_packages(command[1:])
            elif command[0] == "add-bash":
                maker.add_bash_scripts(command[1:])
            elif command[0] == "add-files":
                maker.add_support_files(command[1:])
            elif command[0] == "make":
                maker.make_update_archive()
                break
            elif command[0] == "quit":
                break
            else:
                print("not valid command")
        except Exception as exc:
            print(exc)

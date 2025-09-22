import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Stream and visualize data from the Muse EEG headset.",
        usage="""MuseLSL2 <command> [<args>]
    See https://github.com/DominiqueMakowski/MuseLSL2 for help.
        """,
    )

    parser.add_argument("command", help="Command to run.")

    # parse_args defaults to [1:] for args, but you need to
    # exclude the rest of the args too, or validation will fail
    args = parser.parse_args(sys.argv[1:2])

    from .cli import CLI

    if not hasattr(CLI, args.command):
        print("Incorrect usage. See help below.")
        parser.print_help()
        exit(1)

    cli = CLI(args.command)


if __name__ == "__main__":
    main()

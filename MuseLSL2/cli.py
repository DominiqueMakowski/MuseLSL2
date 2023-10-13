#!/usr/bin/python
import argparse
import sys


class CLI:
    def __init__(self, command):
        # use dispatch pattern to invoke method with same name
        getattr(self, command)()

    def find(self):
        from .find import find_devices

        find_devices(max_duration=10, verbose=True)

    def stream(self):
        parser = argparse.ArgumentParser(
            description="Start an LSL stream from Muse headset."
        )
        parser.add_argument(
            "-a",
            "--address",
            dest="address",
            type=str,
            default=None,
            help="Device MAC address.",
        )
        parser.add_argument(
            "-p",
            "--ppg",
            default=True,
            action="store_false",
            help="Disable streaming of PPG data",
        )
        parser.add_argument(
            "-c",
            "--acc",
            default=True,
            action="store_false",
            help="Disable streaming of accelerometer data",
        )
        parser.add_argument(
            "-g",
            "--gyro",
            default=True,
            action="store_false",
            help="Disable streaming of gyroscope data",
        )

        args = parser.parse_args(sys.argv[2:])
        from .stream import stream

        stream(args.address, args.ppg, args.acc, args.gyro)

    def view(self):
        from .view import view

        view()

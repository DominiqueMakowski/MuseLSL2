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
            "-n",
            "--name",
            dest="name",
            type=str,
            default=None,
            help="Name of the device.",
        )
        parser.add_argument(
            "-i",
            "--interface",
            dest="interface",
            type=str,
            default=None,
            help="The interface to use, 'hci0' for gatt or a com port for bgapi.",
        )
        parser.add_argument(
            "-P",
            "--preset",
            type=int,
            default=None,
            help="Select preset which dictates data channels to be streamed",
        )
        parser.add_argument(
            "-p", "--ppg", default=False, action="store_true", help="Include PPG data"
        )
        parser.add_argument(
            "-c",
            "--acc",
            default=False,
            action="store_true",
            help="Include accelerometer data",
        )
        parser.add_argument(
            "-g",
            "--gyro",
            default=False,
            action="store_true",
            help="Include gyroscope data",
        )
        parser.add_argument(
            "-dl",
            "--disable-light",
            dest="disable_light",
            action="store_true",
            help="Turn off light on the Muse S headband",
        )

        args = parser.parse_args(sys.argv[2:])
        from .stream import stream

        stream(
            args.address,
            args.interface,
            args.name,
            args.ppg,
            args.acc,
            args.gyro,
            args.preset,
            args.disable_light,
        )

    def view(self):
        from .view import view

        view()

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
            "-b",
            "--backend",
            dest="backend",
            type=str,
            default="auto",
            help="BLE backend to use. Can be auto, bluemuse, gatt or bgapi.",
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
            args.backend,
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

    def record(self):
        parser = argparse.ArgumentParser(description="Record data from an LSL stream.")
        parser.add_argument(
            "-d",
            "--duration",
            dest="duration",
            type=int,
            default=60,
            help="Duration of the recording in seconds.",
        )
        parser.add_argument(
            "-f",
            "--filename",
            dest="filename",
            type=str,
            default=None,
            help="Name of the recording file.",
        )
        parser.add_argument(
            "-dj",
            "--dejitter",
            dest="dejitter",
            type=bool,
            default=False,
            help="Whether to apply dejitter correction to timestamps.",
        )
        parser.add_argument(
            "-t",
            "--type",
            type=str,
            default="EEG",
            help="Data type to record from. Either EEG, PPG, ACC, or GYRO.",
        )

        args = parser.parse_args(sys.argv[2:])
        from . import record

        record(args.duration, args.filename, args.dejitter, args.type)

    def record_direct(self):
        parser = argparse.ArgumentParser(
            description="Record directly from Muse without LSL."
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
            "-b",
            "--backend",
            dest="backend",
            type=str,
            default="auto",
            help="BLE backend to use. Can be auto, bluemuse, gatt or bgapi.",
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
            "-d",
            "--duration",
            dest="duration",
            type=int,
            default=60,
            help="Duration of the recording in seconds.",
        )
        parser.add_argument(
            "-f",
            "--filename",
            dest="filename",
            type=str,
            default=None,
            help="Name of the recording file.",
        )
        args = parser.parse_args(sys.argv[2:])
        from . import record_direct

        record_direct(
            args.duration,
            args.address,
            args.filename,
            args.backend,
            args.interface,
            args.name,
        )

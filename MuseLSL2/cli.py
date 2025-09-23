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
        parser.add_argument(
            "-P",
            "--preset",
            default="p50",
            type=str,
            help="Select preset which dictates data channels to be streamed. Default is p50, but can also be 'none'",
        )
        args = parser.parse_args(sys.argv[2:])

        from .stream import stream

        stream(args.address, args.ppg, args.acc, args.gyro, args.preset)

    def view(self):
        from .view import view

        view()

    def inspect(self):
        parser = argparse.ArgumentParser(
            description="Inspect BLE GATT services/characteristics for a device."
        )
        parser.add_argument("--address", "-a", required=True, help="Device MAC address")
        args = parser.parse_args(sys.argv[2:])
        from .backends import BleakBackend

        adapter = BleakBackend()
        dev = adapter.connect(args.address)
        try:
            services = dev.get_services()
            for svc in services:
                print(f"Service {svc.uuid} ({getattr(svc, 'description', '')})")
                for ch in svc.characteristics:
                    props = ",".join(sorted(getattr(ch, "properties", [])))
                    print(
                        f"  Char {ch.uuid} handle={ch.handle} props=[{props}] desc={getattr(ch, 'description', '')}"
                    )
        finally:
            dev.disconnect()

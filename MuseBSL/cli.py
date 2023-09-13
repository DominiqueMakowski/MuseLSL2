import argparse
import sys


class CLI:
    def __init__(self, command):
        # use dispatch pattern to invoke method with same name
        getattr(self, command)()

    def find(self):
        from .find_devices import find_devices

        print("something")

        find_devices()

import bsl

from .backends import BleakBackend
from .find import find_devices


class Muse:
    """Muse EEG headband"""

    def __init__(self, address=None):
        # Create Bluetooth adapter
        self.adapter = BleakBackend()

        # Assign (or find) MAC address
        self.address = address
        if address is None:
            muses = find_devices(max_duration=5, verbose=False)
            if len(muses) == 0:
                print("No Muses found, make sure it's connected.")
            if len(muses) == 1:
                self.address = muses[0]["address"]
            if len(muses) > 1:
                print("Multiple Muses found. Please specify MAC address.")
                self.address = muses[0]["address"]  # Pick first one

    def connect(self):
        self.adapter.start()
        self.device = self.adapter.connect(self.address)
        print(f"Connected to {self.address}.")

    def start(self):
        self.first_sample = True
        self.time_start = bsl.lsl.local_clock()

    def stop(self):
        self.device.disconnect()
        self.adapter.stop()

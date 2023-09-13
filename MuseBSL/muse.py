from .backends import BleakBackend
from .find import find_devices


class Muse:
    """Muse EEG headband"""

    def __init__(self, address=None):
        # Create Bluetooth adapter
        self.adapter = BleakBackend()

        # Assign MAC address
        self.address = address
        if address is None:
            muses = find_devices(max_duration=10, verbose=False)
            if len(muses) == 0:
                print("No Muses found, make sure it's connected.")
            if len(muses) == 1:
                self.address = muses[0]["address"]
            if len(muses) > 1:
                print("Multiple Muses found. Please specify MAC address.")
                self.address = muses[0]["address"]  # Pick first one

    def connect(self):
        self.adapter.start()

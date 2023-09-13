from .backends import BleakBackend


class Muse:
    """Muse EEG headband"""

    def __init__(self, address=None):
        # Create Bluetooth adapter
        self.adapter = BleakBackend()

        # Assign MAC address
        self.address = address
        if address is None:
            muses = self.find(verbose=False)
            if len(muses) == 0:
                print("No Muses found, make sure it's connected.")
            if len(muses) == 1:
                self.address = muses[0]["address"]
            if len(muses) > 1:
                print("Multiple Muses found. Please specify MAC address.")
                self.address = muses[0]["address"]  # Pick first one

    def find(self, max_duration=10, verbose=False):
        self.adapter.start()
        print(f"Searching for Muses (max. {max_duration} seconds)...")
        devices = self.adapter.scan(timeout=10.5)  # Muse scan timeout
        self.adapter.stop()
        muses = [d for d in devices if d["name"] and "Muse" in d["name"]]

        if verbose:
            for m in muses:
                print(f'Found device {m["name"]}, MAC Address {m["address"]}')
            if not muses:
                print("No Muses found, make sure it's connected.")

        return muses

    def connect(self):
        self.adapter.start()

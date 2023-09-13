from .backends import BleakBackend


class Muse:
    """Muse EEG headband"""

    def __init__(self, address=None):
        self.address = address
        self.adapter = BleakBackend()

    def find(self, max_duration=10):
        self.adapter.start()
        print(f"Searching for Muses (max. {max_duration} seconds)...")
        devices = self.adapter.scan(timeout=10.5)  # Muse scan timeout
        self.adapter.stop()
        muses = [d for d in devices if d["name"] and "Muse" in d["name"]]

        for m in muses:
            print(f'Found device {m["name"]}, MAC Address {m["address"]}')
        if not muses:
            print("No Muses found, make sure it's connected.")

        return muses[0]

    def connect(self):
        self.adapter.start()

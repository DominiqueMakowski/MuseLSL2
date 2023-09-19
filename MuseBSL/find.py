from .backends import BleakBackend


def find_devices(max_duration=10, verbose=True):
    adapter = BleakBackend()

    adapter.start()
    print(f"Searching for Muses (max. {max_duration} seconds)...")
    devices = adapter.scan(timeout=max_duration)  # Muse scan timeout
    adapter.stop()
    muses = [d for d in devices if d["name"] and "Muse" in d["name"]]

    if verbose:
        for m in muses:
            print(f'Found device {m["name"]}, MAC Address {m["address"]}')
        if not muses:
            # print("No Muses found, make sure it's connected.")
            raise ConnectionError("No Muses found, make sure it's connected.")
    return muses

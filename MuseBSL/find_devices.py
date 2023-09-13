from .backends import BleakBackend


# Returns a list of available Muse devices.
def find_devices(backend="auto", interface=None):
    print("YES: find_devices")
    adapter = BleakBackend()

    adapter.start()
    print("Searching for Muses, this may take up to 10 seconds...")
    devices = adapter.scan(timeout=10.5)  # Muse scan timeout
    adapter.stop()
    muses = [d for d in devices if d["name"] and "Muse" in d["name"]]

    for m in muses:
        print(f'Found device {m["name"]}, MAC Address {m["address"]}')
    if not muses:
        print("No Muses found.")

    return muses

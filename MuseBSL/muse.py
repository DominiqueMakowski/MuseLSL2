import bitstring
import bsl
import numpy as np

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
        print(f"Connected to Muse ({self.address})...")

    def start(self):
        self.first_sample = True
        # self.time_start = bsl.lsl.local_clock()

    def stop(self):
        self.device.disconnect()
        self.adapter.stop()

    def subscribe_eeg(self):
        """subscribe to eeg stream."""
        # See https://github.com/alexandrebarachant/muse-lsl/blob/master/muselsl/constants.py
        TP9 = "273e0003-4c4d-454d-96be-f03bac821358"  # 0x1f-0x21
        AF7 = "273e0004-4c4d-454d-96be-f03bac821358"  # fp1 0x22-0x24
        AF8 = "273e0005-4c4d-454d-96be-f03bac821358"  # fp2 0x25-0x27
        TP10 = "273e0006-4c4d-454d-96be-f03bac821358"  # 0x28-0x2a
        RIGHTAUX = "273e0007-4c4d-454d-96be-f03bac821358"  # 0x2b-0x2d

        self.device.subscribe(TP9, callback=self._callback_eeg)
        self.device.subscribe(AF7, callback=self._callback_eeg)
        self.device.subscribe(AF8, callback=self._callback_eeg)
        self.device.subscribe(TP10, callback=self._callback_eeg)
        self.device.subscribe(RIGHTAUX, callback=self._callback_eeg)

    # Callbacks
    def _callback_eeg(self, handle, data):
        """Callback for receiving a sample.

        samples are received in this order : 44, 41, 38, 32, 35
        wait until we get 35 and call the data callback
        """
        tm, d = _unpack_eeg_channel(data)


# ==============================================================================
# Utilities
# ==============================================================================
def _unpack_eeg_channel(packet):
    """Decode data packet of one EEG channel.

    Each packet is encoded with a 16bit timestamp followed by 12 time
    samples with a 12 bit resolution.
    """
    aa = bitstring.Bits(bytes=packet)
    pattern = "uint:16,uint:12,uint:12,uint:12,uint:12,uint:12,uint:12, \
                uint:12,uint:12,uint:12,uint:12,uint:12,uint:12"

    res = aa.unpack(pattern)
    index = res[0]
    data = res[1:]
    # 12 bits on a 2 mVpp range
    data = 0.48828125 * (np.array(data) - 2048)
    return index, data

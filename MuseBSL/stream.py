import time

import bsl

from .muse import Muse


def stream(address):
    # Connect
    muse = Muse(address=address)
    muse.connect()

    # Create EEG stream
    info_eeg = bsl.lsl.StreamInfo(
        name="Muse",
        stype="EEG",
        n_channels=5,
        sfreq=256,
        dtype="float32",
        source_id=muse.address,
    )

    # Add additional information
    info_eeg.desc.append_child_value("manufacturer", "Muse")
    eeg_channels = info_eeg.desc.append_child("channels")

    for channel in ["TP9", "AF7", "AF8", "TP10", "Right AUX"]:
        eeg_channels.append_child("channel").append_child_value(
            "label", channel
        ).append_child_value("unit", "microvolts").append_child_value("type", "EEG")

    # Create outlet
    eeg_outlet = bsl.lsl.StreamOutlet(info_eeg, chunk_size=6, max_buffered=360)

    # Start streaming
    muse.start()

    # Loop until interrupted
    # while True:
    while bsl.lsl.local_clock() - muse.time_start < 20:
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            print("interrupted!")
            break

    muse.stop()
    print("Disconnected.")

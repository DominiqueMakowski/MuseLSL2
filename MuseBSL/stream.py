from functools import partial

import bsl.lsl

from . import backends
from .muse import Muse


# Begins LSL stream(s) from a Muse with a given address with data sources determined by arguments
def stream(
    address,
    ppg=True,
    acc_enabled=False,
    gyro_enabled=False,
    disable_light=False,
):
    if not address:
        from .find import find_devices

        device = find_devices(max_duration=10, verbose=True)[0]
        address = device["address"]

    eeg_info = bsl.lsl.StreamInfo(
        "Muse",
        "EEG",
        n_channels=5,
        sfreq=256,
        dtype="float32",
        source_id="Muse%s" % address,
    )
    eeg_info.desc.append_child_value("manufacturer", "Muse")
    eeg_channels = eeg_info.desc.append_child("channels")

    for c in ["TP9", "AF7", "AF8", "TP10", "Right AUX"]:
        eeg_channels.append_child("channel").append_child_value(
            "label", c
        ).append_child_value("unit", "microvolts").append_child_value("type", "EEG")

    eeg_outlet = bsl.lsl.StreamOutlet(eeg_info, chunk_size=12)

    if ppg is True:
        ppg_info = bsl.lsl.StreamInfo(
            "Muse",
            "PPG",
            n_channels=3,
            sfreq=64,
            dtype="float32",
            source_id="Muse%s" % address,
        )
        ppg_info.desc.append_child_value("manufacturer", "Muse")
        ppg_channels = ppg_info.desc.append_child("channels")

        # PPG data has three channels: ambient, infrared, red
        for c in ["LUX", "PPG", "RED"]:
            ppg_channels.append_child("channel").append_child_value(
                "label", c
            ).append_child_value("unit", "mmHg").append_child_value("type", "PPG")

        ppg_outlet = bsl.lsl.StreamOutlet(ppg_info, chunk_size=6)

    if acc_enabled:
        acc_info = bsl.lsl.StreamInfo(
            "Muse",
            "ACC",
            n_channels=3,
            sfreq=52,
            dtype="float32",
            source_id="Muse%s" % address,
        )
        acc_info.desc.append_child_value("manufacturer", "Muse")
        acc_channels = acc_info.desc.append_child("channels")

        for c in ["ACC_X", "ACC_Y", "ACC_Z"]:
            acc_channels.append_child("channel").append_child_value(
                "label", c
            ).append_child_value("unit", "g").append_child_value(
                "type", "accelerometer"
            )

        acc_outlet = bsl.lsl.StreamOutlet(acc_info, chunk_size=1)

    if gyro_enabled:
        gyro_info = bsl.lsl.StreamInfo(
            "Muse",
            "GYRO",
            n_channels=3,
            sfreq=52,
            dtype="float32",
            source_id="Muse%s" % address,
        )
        gyro_info.desc.append_child_value("manufacturer", "Muse")
        gyro_channels = gyro_info.desc.append_child("channels")

        for c in ["GYRO_X", "GYRO_Y", "GYRO_Z"]:
            gyro_channels.append_child("channel").append_child_value(
                "label", c
            ).append_child_value("unit", "dps").append_child_value("type", "gyroscope")

        gyro_outlet = bsl.lsl.StreamOutlet(gyro_info, chunk_size=1)

    def push(data, timestamps, outlet):
        for ii in range(data.shape[1]):
            outlet.push_sample(data[:, ii], timestamps[ii])

    push_eeg = partial(push, outlet=eeg_outlet)
    push_ppg = partial(push, outlet=ppg_outlet) if ppg else None
    push_acc = partial(push, outlet=acc_outlet) if acc_enabled else None
    push_gyro = partial(push, outlet=gyro_outlet) if gyro_enabled else None

    muse = Muse(
        address=address,
        callback_eeg=push_eeg,
        callback_ppg=push_ppg,
        callback_acc=push_acc,
        callback_gyro=push_gyro,
        disable_light=disable_light,
    )

    didConnect = muse.connect()

    if didConnect:
        print("Connected.")
        muse.start()

        ppg_string = ", PPG" if ppg else ""
        acc_string = ", ACC" if acc_enabled else ""
        gyro_string = ", GYRO" if gyro_enabled else ""

        print(
            f"Streaming... EEG{ppg_string}{acc_string}{gyro_string}... (CTRL + C to interrupt)"
        )

        # Disconnect if no data is received for 60 seconds
        while bsl.lsl.local_clock() - muse.last_timestamp < 60:
            try:
                backends.sleep(1)
            except KeyboardInterrupt:
                muse.stop()
                print("Stream interrupted. Stopping...")
                break

        if bsl.lsl.local_clock() - muse.last_timestamp > 60:
            print("No data received since 1 min. Disconnecting...")
        print("Disconnected.")

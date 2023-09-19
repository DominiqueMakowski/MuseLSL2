import re
import subprocess
import time
from functools import partial
from shutil import which
from sys import platform

from pylsl import StreamInfo, StreamOutlet

from .backends import bleak_sleep
from .constants import (
    AUTO_DISCONNECT_DELAY,
    LSL_ACC_CHUNK,
    LSL_EEG_CHUNK,
    LSL_GYRO_CHUNK,
    LSL_PPG_CHUNK,
    MUSE_NB_ACC_CHANNELS,
    MUSE_NB_EEG_CHANNELS,
    MUSE_NB_GYRO_CHANNELS,
    MUSE_NB_PPG_CHANNELS,
    MUSE_SAMPLING_ACC_RATE,
    MUSE_SAMPLING_EEG_RATE,
    MUSE_SAMPLING_GYRO_RATE,
    MUSE_SAMPLING_PPG_RATE,
)
from .muse import Muse


# Begins LSL stream(s) from a Muse with a given address with data sources determined by arguments
def stream(
    address,
    interface=None,
    name=None,
    ppg_enabled=False,
    acc_enabled=False,
    gyro_enabled=False,
    disable_light=False,
    timeout=AUTO_DISCONNECT_DELAY,
):
    if not address:
        from .find import find_devices

        device = find_devices(max_duration=10, verbose=True)[0]
        address = device["address"]
        name = device["name"]

    eeg_info = StreamInfo(
        "Muse",
        "EEG",
        MUSE_NB_EEG_CHANNELS,
        MUSE_SAMPLING_EEG_RATE,
        "float32",
        "Muse%s" % address,
    )
    eeg_info.desc().append_child_value("manufacturer", "Muse")
    eeg_channels = eeg_info.desc().append_child("channels")

    for c in ["TP9", "AF7", "AF8", "TP10", "Right AUX"]:
        eeg_channels.append_child("channel").append_child_value(
            "label", c
        ).append_child_value("unit", "microvolts").append_child_value("type", "EEG")

    eeg_outlet = StreamOutlet(eeg_info, LSL_EEG_CHUNK)

    if ppg_enabled:
        ppg_info = StreamInfo(
            "Muse",
            "PPG",
            MUSE_NB_PPG_CHANNELS,
            MUSE_SAMPLING_PPG_RATE,
            "float32",
            "Muse%s" % address,
        )
        ppg_info.desc().append_child_value("manufacturer", "Muse")
        ppg_channels = ppg_info.desc().append_child("channels")

        for c in ["PPG1", "PPG2", "PPG3"]:
            ppg_channels.append_child("channel").append_child_value(
                "label", c
            ).append_child_value("unit", "mmHg").append_child_value("type", "PPG")

        ppg_outlet = StreamOutlet(ppg_info, LSL_PPG_CHUNK)

    if acc_enabled:
        acc_info = StreamInfo(
            "Muse",
            "ACC",
            MUSE_NB_ACC_CHANNELS,
            MUSE_SAMPLING_ACC_RATE,
            "float32",
            "Muse%s" % address,
        )
        acc_info.desc().append_child_value("manufacturer", "Muse")
        acc_channels = acc_info.desc().append_child("channels")

        for c in ["X", "Y", "Z"]:
            acc_channels.append_child("channel").append_child_value(
                "label", c
            ).append_child_value("unit", "g").append_child_value(
                "type", "accelerometer"
            )

        acc_outlet = StreamOutlet(acc_info, LSL_ACC_CHUNK)

    if gyro_enabled:
        gyro_info = StreamInfo(
            "Muse",
            "GYRO",
            MUSE_NB_GYRO_CHANNELS,
            MUSE_SAMPLING_GYRO_RATE,
            "float32",
            "Muse%s" % address,
        )
        gyro_info.desc().append_child_value("manufacturer", "Muse")
        gyro_channels = gyro_info.desc().append_child("channels")

        for c in ["X", "Y", "Z"]:
            gyro_channels.append_child("channel").append_child_value(
                "label", c
            ).append_child_value("unit", "dps").append_child_value("type", "gyroscope")

        gyro_outlet = StreamOutlet(gyro_info, LSL_GYRO_CHUNK)

    def push(data, timestamps, outlet):
        for ii in range(data.shape[1]):
            outlet.push_sample(data[:, ii], timestamps[ii])

    push_eeg = partial(push, outlet=eeg_outlet)
    push_ppg = partial(push, outlet=ppg_outlet) if ppg_enabled else None
    push_acc = partial(push, outlet=acc_outlet) if acc_enabled else None
    push_gyro = partial(push, outlet=gyro_outlet) if gyro_enabled else None

    muse = Muse(
        address=address,
        callback_eeg=push_eeg,
        callback_ppg=push_ppg,
        callback_acc=push_acc,
        callback_gyro=push_gyro,
        name=name,
        disable_light=disable_light,
    )

    didConnect = muse.connect()

    if didConnect:
        print("Connected.")
        muse.start()

        ppg_string = ", PPG" if ppg_enabled else ""
        acc_string = ", ACC" if acc_enabled else ""
        gyro_string = ", GYRO" if gyro_enabled else ""

        print(
            f"Streaming... EEG{ppg_string}{acc_string}{gyro_string}... (CTRL + C to interrupt)"
        )

        while time.time() - muse.last_timestamp < timeout:
            try:
                bleak_sleep(1)
            except KeyboardInterrupt:
                muse.stop()
                print("Stream interrupted. Stopping...")
                break

        print("Disconnected.")

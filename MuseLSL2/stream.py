from functools import partial

from . import backends


def stream(address, ppg=True, acc=True, gyro=True, preset=None):
    import mne_lsl.lsl
    from .muse import Muse

    # Find device
    if not address:
        from .find import find_devices

        device = find_devices(max_duration=10, verbose=True)[0]
        address = device["address"]

    # EEG ====================================================
    eeg_info = mne_lsl.lsl.StreamInfo(
        "Muse",
        stype="EEG",
        n_channels=5,
        sfreq=256,
        dtype="float32",
        source_id=f"Muse_{address}",
    )
    eeg_info.desc.append_child_value("manufacturer", "Muse")
    eeg_info.set_channel_names(["TP9", "AF7", "AF8", "TP10", "AUX"])
    eeg_info.set_channel_types(["eeg"] * 5)
    eeg_info.set_channel_units("microvolts")

    eeg_outlet = mne_lsl.lsl.StreamOutlet(eeg_info, chunk_size=6)

    # PPG ====================================================
    ppg_outlet = None
    if ppg is True:
        ppg_info = mne_lsl.lsl.StreamInfo(
            "Muse",
            stype="PPG",
            n_channels=3,
            sfreq=64,
            dtype="float32",
            source_id=f"Muse_{address}",
        )
        ppg_info.desc.append_child_value("manufacturer", "Muse")
        # PPG data has three channels: ambient, infrared, red
        ppg_info.set_channel_names(["LUX", "IR", "RED"])
        ppg_info.set_channel_types(["ppg"] * 3)
        ppg_info.set_channel_units("mmHg")

        if ppg_info is not None:
            ppg_outlet = mne_lsl.lsl.StreamOutlet(ppg_info, chunk_size=1)

    # ACC ====================================================
    acc_outlet = None
    if acc:
        acc_info = mne_lsl.lsl.StreamInfo(
            "Muse",
            stype="ACC",
            n_channels=3,
            sfreq=52,
            dtype="float32",
            source_id=f"Muse_{address}",
        )
        acc_info.desc.append_child_value("manufacturer", "Muse")
        acc_info.set_channel_names(["ACC_X", "ACC_Y", "ACC_Z"])
        acc_info.set_channel_types(["accelerometer"] * 3)
        acc_info.set_channel_units("g")

        if acc_info is not None:
            acc_outlet = mne_lsl.lsl.StreamOutlet(acc_info, chunk_size=1)

    # GYRO ====================================================
    gyro_outlet = None
    if gyro:
        gyro_info = mne_lsl.lsl.StreamInfo(
            "Muse",
            stype="GYRO",
            n_channels=3,
            sfreq=52,
            dtype="float32",
            source_id=f"Muse_{address}",
        )
        gyro_info.desc.append_child_value("manufacturer", "Muse")
        gyro_info.set_channel_names(["GYRO_X", "GYRO_Y", "GYRO_Z"])
        gyro_info.set_channel_types(["gyroscope"] * 3)
        gyro_info.set_channel_units("dps")

        if gyro_info is not None:
            gyro_outlet = mne_lsl.lsl.StreamOutlet(gyro_info, chunk_size=1)

    def push(data, timestamps, outlet):
        outlet.push_chunk(data.T, timestamps[-1])

    push_eeg = partial(push, outlet=eeg_outlet)
    push_ppg = partial(push, outlet=ppg_outlet) if ppg else None
    push_acc = partial(push, outlet=acc_outlet) if acc else None
    push_gyro = partial(push, outlet=gyro_outlet) if gyro else None

    muse = Muse(
        address=address,
        callback_eeg=push_eeg,
        callback_ppg=push_ppg,
        callback_acc=push_acc,
        callback_gyro=push_gyro,
        preset=preset,
    )

    didConnect = muse.connect()

    if didConnect:
        print("Connected.")
        muse.start()

        ppg_txt = ", PPG" if ppg else ""
        acc_txt = ", ACC" if acc else ""
        gyro_txt = ", GYRO" if gyro else ""

        print(
            f"Streaming... EEG{ppg_txt}{acc_txt}{gyro_txt}... (CTRL + C to interrupt)"
        )

        # Disconnect if no data is received for 60 seconds
        while mne_lsl.lsl.local_clock() - muse.last_timestamp < 60:
            try:
                backends.sleep(1)
            except KeyboardInterrupt:
                try:
                    muse.stop()
                except Exception:
                    pass
                print("Stream interrupted. Stopping...")
                break

        if mne_lsl.lsl.local_clock() - muse.last_timestamp > 60:
            print("No data received for 60 seconds. Disconnecting...")
        print("Disconnected.")

import bsl


def stream(address):
    print("A")
    info_eeg = bsl.lsl.StreamInfo(
        name="Muse",
        stype="EEG",
        n_channels=5,
        sfreq=256,
        dtype="float32",
        source_id=address,
    )
    print("B")
    # Add additional information

    info_eeg.desc().append_child_value("manufacturer", "Muse")
    eeg_channels = info_eeg.desc().append_child("channels")

    for channel in ["TP9", "AF7", "AF8", "TP10", "Right AUX"]:
        eeg_channels.append_child("channel").append_child_value(
            "label", channel
        ).append_child_value("unit", "microvolts").append_child_value("type", "EEG")

    print(info_eeg.desc())
    eeg_outlet = bsl.lsl.StreamOutlet(info_eeg, 12)
    print(eeg_outlet)

# MuseLSL2

This is a light reimplementation of [muse-lsl](https://github.com/alexandrebarachant/muse-lsl/) with a few improvements:

- [x] Fixed [timestamps correctness](https://github.com/alexandrebarachant/muse-lsl/pull/197).
- [x] Uses [mne-lsl](https://github.com/mne-tools/mne-lsl), which is an upgraded version of the LSL interface.
- [x] Viewer also shows PPG and related channels.
- [x] Fixed timeout issue and disconnection (to be confirmed)

![](MuseLSL2_viewer.gif)

By default, MuseLSL2 streams *all* channels (including gyroscope, accelerometer, and the signal form the Auxiliary port "AUX", which can be used to add [an additional electrode](https://github.com/andrewjsauer/Muse-EEG-Extra-Electrode-Tutorial)). Note that without an additional electrode, the AUX channel will just pick up noise and should be discarded.


## Muse S Athena (experimental)

- Initial support is added for the new "Muse S Athena" devices that expose a combined EEG characteristic.
- If detected, the package subscribes to `273e0013-4c4d-454d-96be-f03bac821358` and attempts to decode 5x12 EEG frames similarly to legacy devices. This is based on public notes from BrainFlow PR #779 and may change.
- Use `MuseLSL2 inspect --address <MAC>` to list GATT services and confirm whether the device exposes the combined EEG characteristic.
- Start with preset `p21` or `p1045` to enable EEG only; broader sensor support is still under investigation.
If streaming fails, please share the output of the `inspect` command and any console logs.

## Usage

Install with:

```
pip install https://github.com/DominiqueMakowski/MuseLSL2/zipball/main
```

Power up Muse EEG headset, Open console, run:

```
MuseLSL2 find
```

Once you have the mac address of your device, run for instance (but replace the address):

```
MuseLSL2 stream --address 00:55:DA:B5:E8:CF

For Athena devices, you can also try forcing an EEG-only preset first:

```
MuseLSL2 stream --address 00:55:DA:B5:E8:CF --preset p21
```
```

In a new console, while streaming, run:

```
MuseLSL2 view
```

## Record

Best is to record the streams using [Lab Recorder](https://github.com/labstreaminglayer/App-LabRecorder).


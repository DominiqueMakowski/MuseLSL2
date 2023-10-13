# MuseLSL2

This is a light reimplementation of [muse-lsl](https://github.com/alexandrebarachant/muse-lsl/) with a few improvements:

- [x] Fixed [timestamps correctness](https://github.com/alexandrebarachant/muse-lsl/pull/197).
- [x] Uses [mne-lsl](https://github.com/mne-tools/mne-lsl), which is an upgraded version of the LSL interface.
- [x] Viewer also shows PPG and related channels.
- [x] Fixed timeout issue and disconnection (to be confirmed)

![](MuseLSL2_viewer.gif)

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
```

In a new console, while streaming, run:

```
MuseLSL2 view
```
import bitstring
import mne_lsl.lsl
import numpy as np
from typing import cast

from .backends import BleakBackend

# Constants (see https://mind-monitor.com/forums/viewtopic.php?t=1760)
# ---------------------------------------------------------------------------------------------
# 00001800-0000-1000-8000-00805f9b34fb Generic Access 0x05-0x0b
# 00001801-0000-1000-8000-00805f9b34fb Generic Attribute 0x01-0x04
ATTR_SERVICECHANGED = "00002a05-0000-1000-8000-00805f9b34fb"  # ble std 0x02-0x04
# 0000fe8d-0000-1000-8000-00805f9b34fb Interaxon Inc. 0x0c-0x42
ATTR_STREAM_TOGGLE = "273e0001-4c4d-454d-96be-f03bac821358"  # serial 0x0d-0x0f
ATTR_LEFTAUX = "273e0002-4c4d-454d-96be-f03bac821358"  # not implemented yet 0x1c-0x1e
ATTR_TP9 = "273e0003-4c4d-454d-96be-f03bac821358"  # 0x1f-0x21
ATTR_AF7 = "273e0004-4c4d-454d-96be-f03bac821358"  # fp1 0x22-0x24
ATTR_AF8 = "273e0005-4c4d-454d-96be-f03bac821358"  # fp2 0x25-0x27
ATTR_TP10 = "273e0006-4c4d-454d-96be-f03bac821358"  # 0x28-0x2a
ATTR_RIGHTAUX = "273e0007-4c4d-454d-96be-f03bac821358"  # 0x2b-0x2d
ATTR_REFDRL = "273e0008-4c4d-454d-96be-f03bac821358"  # not implemented yet 0x10-0x12
ATTR_GYRO = "273e0009-4c4d-454d-96be-f03bac821358"  # 0x13-0x15
ATTR_ACCELEROMETER = "273e000a-4c4d-454d-96be-f03bac821358"  # 0x16-0x18
ATTR_TELEMETRY = "273e000b-4c4d-454d-96be-f03bac821358"  # 0x19-0x1b
# ATTR_MAGNETOMETER = '273e000c-4c4d-454d-96be-f03bac821358' # 0x2e-0x30
# ATTR_PRESSURE = '273e000d-4c4d-454d-96be-f03bac821358' # 0x31-0x33
# ATTR_ULTRAVIOLET = '273e000e-4c4d-454d-96be-f03bac821358' # 0x34-0x36
ATTR_PPG1 = "273e000f-4c4d-454d-96be-f03bac821358"  # ambient 0x37-0x39
ATTR_PPG2 = "273e0010-4c4d-454d-96be-f03bac821358"  # infrared 0x3a-0x3c
ATTR_PPG3 = "273e0011-4c4d-454d-96be-f03bac821358"  # red 0x3d-0x3f
ATTR_THERMISTOR = (
    "273e0012-4c4d-454d-96be-f03bac821358"  # muse S only, not implemented yet 0x40-0x42
)


class Muse:
    """Muse EEG headband"""

    def __init__(
        self,
        address,
        callback_eeg=None,
        callback_control=None,
        callback_telemetry=None,
        callback_acc=None,
        callback_gyro=None,
        callback_ppg=None,
        preset=None,
        disable_light=False,
    ):
        """Initialize

        callback_eeg -- callback for eeg data, function(data, timestamps)
        callback_control -- function(message)
        callback_telemetry -- function(timestamp, battery, fuel_gauge,
                                       adc_volt, temperature)

        callback_acc -- function(timestamp, samples)
        callback_gyro -- function(timestamp, samples)
        - samples is a list of 3 samples, where each sample is [x, y, z]
        """

        self.address = address
        self.callback_eeg = callback_eeg
        self.callback_telemetry = callback_telemetry
        self.callback_control = callback_control
        self.callback_acc = callback_acc
        self.callback_gyro = callback_gyro
        self.callback_ppg = callback_ppg

        self.enable_eeg = not callback_eeg is None
        self.enable_control = not callback_control is None
        self.enable_telemetry = not callback_telemetry is None
        self.enable_acc = not callback_acc is None
        self.enable_gyro = not callback_gyro is None
        self.enable_ppg = not callback_ppg is None

        self.preset = preset
        self.disable_light = disable_light

    def connect(self):
        """Connect to the device"""
        print(f"Connecting to {self.address}...")
        self.adapter = BleakBackend()
        self.adapter.start()
        self.device = self.adapter.connect(self.address)

        # Send a preset to the device to enable some functionalities
        if self.preset and self.preset not in ["none", "None"]:
            self.select_preset(self.preset)

        # subscribes to EEG stream
        if self.enable_eeg:
            self._subscribe_eeg()

        if self.enable_control:
            self._subscribe_control()

        if self.enable_telemetry:
            self._subscribe_telemetry()

        if self.enable_acc:
            self._subscribe_acc()

        if self.enable_gyro:
            self._subscribe_gyro()

        if self.enable_ppg:
            self._subscribe_ppg()

        if self.disable_light:
            self._disable_light()

        self.last_timestamp = mne_lsl.lsl.local_clock()

        return True

    def _write_cmd(self, cmd):
        """Wrapper to write a command to the Muse device.
        cmd -- list of bytes"""
        # Write to the control/stream toggle characteristic by UUID to be robust
        # across devices where handles differ (e.g., Muse Athena).
        self.device.char_write_uuid(ATTR_STREAM_TOGGLE, cmd, False)

    def _write_cmd_str(self, cmd):
        """Wrapper to encode and write a command string to the Muse device.
        cmd -- string to send"""
        self._write_cmd([len(cmd) + 1, *(ord(char) for char in cmd), ord("\n")])

    def ask_control(self):
        """Send a message to Muse to ask for the control status.

        Only useful if control is enabled (to receive the answer!)

        The message received is a dict with the following keys:
        "hn": device name
        "sn": serial number
        "ma": MAC address
        "id":
        "bp": battery percentage
        "ts":
        "ps": preset selected
        "rc": return status, if 0 is OK
        """
        self._write_cmd_str("s")

    def ask_device_info(self):
        """Send a message to Muse to ask for the device info.

        The message received is a dict with the following keys:
        "ap":
        "sp":
        "tp": firmware type, e.g: "consumer"
        "hw": hardware version?
        "bn": build number?
        "fw": firmware version?
        "bl":
        "pv": protocol version?
        "rc": return status, if 0 is OK
        """
        self._write_cmd_str("v1")

    def ask_reset(self):
        """Undocumented command reset for '*1'
        The message received is a singleton with:
        "rc": return status, if 0 is OK
        """
        self._write_cmd_str("*1")

    def start(self):
        """Start streaming."""
        self.first_sample = True
        self._init_sample()
        self._init_ppg_sample()
        self.last_tm = 0
        self.last_tm_ppg = 0
        self._init_control()
        self.resume()

    def resume(self):
        """Resume streaming, sending 'd' command"""
        self._write_cmd_str("d")

    def stop(self):
        """Stop streaming."""
        self._write_cmd_str("h")

    def keep_alive(self):
        """Keep streaming, sending 'k' command"""
        self._write_cmd_str("k")

    def select_preset(self, preset="p50"):
        """Set preset for headband configuration

        See details here https://articles.jaredcamins.com/figuring-out-bluetooth-low-energy-part-2-750565329a7d
        For 2016 headband, possible choice are 'p20' and 'p21'.

        p20 - 5-Channel EEG channel streaming
        p21 - 4-Channel EEG channel streaming
        p22 - 4-Channel EEG channel streaming without accel/gyro
        p23 = only 5 eeg
        p31 = weird
        p32 = weird
        p50 = Same as 20, but includes PPG data
        p51 = Same as 21, but includes PPG data
        Untested but possible values include 'p22','p23','p31','p32','p50','p51','p52','p53','p60','p61','p63','pAB','pAD'
        Default is 'p50'."""

        if type(preset) is int:
            preset = str(preset)
        if preset[0] == "p":
            preset = preset[1:]
        preset = bytes(preset, "utf-8")
        self._write_cmd([0x04, 0x70, *preset, 0x0A])

    def disconnect(self):
        """disconnect."""
        self.device.disconnect()
        if self.adapter:
            self.adapter.stop()

    def _subscribe_eeg(self):
        """subscribe to eeg stream."""
        # Bind channel index at subscription time to avoid relying on value handles
        missing = []
        mapping = [
            (ATTR_TP9, 0),
            (ATTR_AF7, 1),
            (ATTR_AF8, 2),
            (ATTR_TP10, 3),
            (ATTR_RIGHTAUX, 4),
        ]
        for uuid, idx in mapping:
            if hasattr(
                self.device, "has_characteristic"
            ) and not self.device.has_characteristic(uuid):
                missing.append(uuid)
            else:
                self.device.subscribe(
                    uuid, callback=lambda h, d, i=idx: self._handle_eeg_idx(i, h, d)
                )
        if missing:
            print("EEG characteristics not found on this device:")
            for u in missing:
                print(f" - {u}")
            print(
                "Run 'MuseLSL2 inspect --address <MAC>' to list available characteristics."
            )

    def _unpack_eeg_channel(self, packet):
        """Decode data packet of one EEG channel.

        Each packet is encoded with a 16bit timestamp followed by 12 time
        samples with a 12 bit resolution.
        """
        aa = bitstring.Bits(bytes=packet)
        pattern = (
            "uint:16,uint:12,uint:12,uint:12,uint:12,uint:12,uint:12, "
            "uint:12,uint:12,uint:12,uint:12,uint:12,uint:12"
        )
        res = aa.unpack(pattern)
        packet_index = cast(int, res[0])
        data = res[1:]
        # 12 bits on a 2 mVpp range
        data = 0.48828125 * (np.array(data) - 2048)
        return packet_index, data

    def _init_sample(self):
        """initialize array to store the samples"""
        self.timestamps = np.full(5, np.nan)
        self.data = np.zeros((5, 12))

    def _init_ppg_sample(self):
        """Initialise array to store PPG samples

        Must be separate from the EEG packets since they occur with a different sampling rate. Ideally the counters
        would always match, but this is not guaranteed
        """
        self.timestamps_ppg = np.full(3, np.nan)
        self.data_ppg = np.zeros((3, 6))

    def _init_timestamp_correction(self):
        """Init IRLS params"""
        # initial params for the timestamp correction
        # the time it started + the inverse of sampling rate
        self.sample_index = 0
        self.sample_index_ppg = 0
        self._P = 1e-4
        t0 = mne_lsl.lsl.local_clock()
        self.reg_params = np.array([t0, 1.0 / 256])  # EEG Sampling Rate = 256 Hz
        self.reg_ppg_sample_rate = np.array([t0, 1.0 / 64])  # PPG Sampling Rate = 64 Hz

    def _update_timestamp_correction(self, t_source, t_receiver):
        """Update regression for dejittering

        This is based on Recursive least square.
        See https://arxiv.org/pdf/1308.3846.pdf.
        """

        # remove the offset
        t_receiver = t_receiver - self.reg_params[0]

        # least square estimation
        P = self._P
        R = self.reg_params[1]
        P = P - ((P**2) * (t_source**2)) / (1 - (P * (t_source**2)))
        R = R + P * t_source * (t_receiver - t_source * R)

        # update parameters
        self.reg_params[1] = R
        self._P = P

    def _handle_eeg_idx(self, index, handle, data):
        """Callback for receiving a sample.

        samples are received in this order : 44, 41, 38, 32, 35
        wait until we get 35 and call the data callback
        """
        if self.first_sample:
            self._init_timestamp_correction()
            self.first_sample = False

        timestamp = mne_lsl.lsl.local_clock()
        tm, d = self._unpack_eeg_channel(data)

        if self.last_tm == 0:
            self.last_tm = tm - 1

        self.data[index] = d
        self.timestamps[index] = timestamp
        # When we've received all 5 channel packets, push a frame
        if not np.isnan(self.timestamps).any():
            if tm != self.last_tm + 1:
                if (tm - self.last_tm) != -65535:  # counter reset
                    print("missing sample %d : %d" % (tm, self.last_tm))
                    # correct sample index for timestamp estimation
                    self.sample_index += 12 * (tm - self.last_tm + 1)

            self.last_tm = tm

            # calculate index of time samples
            idxs = np.arange(0, 12) + self.sample_index
            self.sample_index += 12

            # update timestamp correction based on earliest packet timestamp
            self._update_timestamp_correction(idxs[-1], np.nanmin(self.timestamps))

            # timestamps are extrapolated based on sampling rate and start time
            timestamps = self.reg_params[1] * idxs + self.reg_params[0]

            # push data
            if self.callback_eeg:
                self.callback_eeg(self.data, timestamps)

            # save last timestamp for disconnection timer
            self.last_timestamp = timestamps[-1]

            # reset sample
            self._init_sample()

    def _init_control(self):
        """Variable to store the current incoming message."""
        self._current_msg = ""

    def _subscribe_control(self):
        self.device.subscribe(ATTR_STREAM_TOGGLE, callback=self._handle_control)

        self._init_control()

    def _handle_control(self, handle, packet):
        """Handle the incoming messages from the 0x000e handle.

        Each message is 20 bytes
        The first byte, call it n, is the length of the incoming string.
        The rest of the bytes are in ASCII, and only n chars are useful

        Multiple messages together are a json object (or dictionary in python)
        If a message has a '}' then the whole dict is finished.

        Example:
        {'key': 'value',
        'key2': 'really-long
        -value',
        'key3': 'value3'}

        each line is a message, the 4 messages are a json object.
        """
        # No handle guard; subscription is bound by UUID
        data_bytes = bytes(packet)
        if not data_bytes:
            return
        n_incoming = data_bytes[0]
        incoming_message = data_bytes[1 : 1 + n_incoming].decode(
            "ascii", errors="ignore"
        )

        # Add to current message
        self._current_msg += incoming_message

        if incoming_message[-1] == "}":  # Message ended completely
            if self.callback_control:
                self.callback_control(self._current_msg)

            self._init_control()

    def _subscribe_telemetry(self):
        if hasattr(
            self.device, "has_characteristic"
        ) and not self.device.has_characteristic(ATTR_TELEMETRY):
            print(f"TELEMETRY characteristic not found: {ATTR_TELEMETRY}")
            print("Run 'MuseLSL2 inspect --address <MAC>' to discover proper UUID.")
            return
        self.device.subscribe(ATTR_TELEMETRY, callback=self._handle_telemetry)

    def _handle_telemetry(self, handle, packet):
        """Handle the telemetry (battery, temperature and stuff) incoming data"""
        timestamp = mne_lsl.lsl.local_clock()

        bit_decoder = bitstring.Bits(bytes=packet)
        pattern = "uint:16,uint:16,uint:16,uint:16,uint:16"  # The rest is 0 padding
        data = bit_decoder.unpack(pattern)
        battery = float(cast(int, data[1])) / 512.0
        fuel_gauge = float(cast(int, data[2])) * 2.2
        adc_volt = cast(int, data[3])
        temperature = cast(int, data[4])

        if self.callback_telemetry:
            self.callback_telemetry(
                timestamp, battery, fuel_gauge, adc_volt, temperature
            )

    def _unpack_imu_channel(self, packet, scale: float = 1.0):
        """Decode data packet of the accelerometer and gyro (imu) channels.

        Each packet is encoded with a 16bit timestamp followed by 9 samples
        with a 16 bit resolution.
        """
        bit_decoder = bitstring.Bits(bytes=packet)
        pattern = (
            "uint:16,int:16,int:16,int:16,int:16, " "int:16,int:16,int:16,int:16,int:16"
        )
        data = bit_decoder.unpack(pattern)
        packet_index = cast(int, data[0])
        samples = np.array(data[1:], dtype=float).reshape((3, 3), order="F") * float(
            scale
        )
        return packet_index, samples

    def _subscribe_acc(self):
        if hasattr(
            self.device, "has_characteristic"
        ) and not self.device.has_characteristic(ATTR_ACCELEROMETER):
            print(f"ACC characteristic not found: {ATTR_ACCELEROMETER}")
            print("Run 'MuseLSL2 inspect --address <MAC>' to discover proper UUID.")
            return
        self.device.subscribe(ATTR_ACCELEROMETER, callback=self._handle_acc)

    def _handle_acc(self, handle, packet):
        """Handle incoming accelerometer data.

        sampling rate: ~17 x second (3 samples in each message, roughly 50Hz)"""
        timestamps = [mne_lsl.lsl.local_clock()] * 3

        # save last timestamp for disconnection timer
        self.last_timestamp = timestamps[-1]

        # MUSE_ACCELEROMETER_SCALE_FACTOR (no idea where this comes from)
        packet_index, samples = self._unpack_imu_channel(packet, scale=0.0000610352)

        if self.callback_acc:
            self.callback_acc(samples, timestamps)

    def _subscribe_gyro(self):
        if hasattr(
            self.device, "has_characteristic"
        ) and not self.device.has_characteristic(ATTR_GYRO):
            print(f"GYRO characteristic not found: {ATTR_GYRO}")
            print("Run 'MuseLSL2 inspect --address <MAC>' to discover proper UUID.")
            return
        self.device.subscribe(ATTR_GYRO, callback=self._handle_gyro)

    def _handle_gyro(self, handle, packet):
        """Handle incoming gyroscope data.

        sampling rate: ~17 x second (3 samples in each message, roughly 50Hz)"""
        timestamps = [mne_lsl.lsl.local_clock()] * 3

        # save last timestamp for disconnection timer
        self.last_timestamp = timestamps[-1]

        # MUSE_GYRO_SCALE_FACTOR (no idea where this number comes from)
        packet_index, samples = self._unpack_imu_channel(packet, scale=0.0074768)

        if self.callback_gyro:
            self.callback_gyro(samples, timestamps)

    def _subscribe_ppg(self):
        """subscribe to ppg stream."""
        mapping = [(ATTR_PPG1, 0), (ATTR_PPG2, 1), (ATTR_PPG3, 2)]
        missing = []
        for uuid, idx in mapping:
            if hasattr(
                self.device, "has_characteristic"
            ) and not self.device.has_characteristic(uuid):
                missing.append(uuid)
            else:
                self.device.subscribe(
                    uuid, callback=lambda h, d, i=idx: self._handle_ppg_idx(i, h, d)
                )
        if missing:
            print("PPG characteristics not found on this device:")
            for u in missing:
                print(f" - {u}")
            print(
                "Run 'MuseLSL2 inspect --address <MAC>' to list available characteristics."
            )

    def _handle_ppg_idx(self, index, handle, data):
        """Callback for receiving a sample.

        samples are received in this order : 56, 59, 62
        wait until we get x and call the data callback
        """
        timestamp = mne_lsl.lsl.local_clock()
        tm, d = self._unpack_ppg_channel(data)

        if self.last_tm_ppg == 0:
            self.last_tm_ppg = tm - 1

        self.data_ppg[index] = d
        self.timestamps_ppg[index] = timestamp
        # When we've received all 3 channel packets, push a frame
        if not np.isnan(self.timestamps_ppg).any():
            if tm != self.last_tm_ppg + 1:
                print("missing sample %d : %d" % (tm, self.last_tm_ppg))
            self.last_tm_ppg = tm

            # calculate index of time samples
            idxs = np.arange(0, 6) + self.sample_index_ppg
            self.sample_index_ppg += 6

            # timestamps are extrapolated backwards based on sampling rate and current time
            timestamps = (
                self.reg_ppg_sample_rate[1] * idxs + self.reg_ppg_sample_rate[0]
            )

            # save last timestamp for disconnection timer
            self.last_timestamp = timestamps[-1]

            # push data
            if self.callback_ppg:
                self.callback_ppg(self.data_ppg, timestamps)

            # reset sample
            self._init_ppg_sample()

    def _unpack_ppg_channel(self, packet):
        """Decode data packet of one PPG channel.
        Each packet is encoded with a 16bit timestamp followed by 3
        samples with an x bit resolution.
        """
        aa = bitstring.Bits(bytes=packet)
        pattern = "uint:16,uint:24,uint:24,uint:24,uint:24,uint:24,uint:24"
        res = aa.unpack(pattern)
        packet_index = cast(int, res[0])
        data = np.array(res[1:], dtype=float)
        return packet_index, data

    def _disable_light(self):
        self._write_cmd_str("L0")

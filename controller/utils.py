import board
import digitalio
import io
import msgpack
import pwmio
import struct
import supervisor
import time
import usb_hid
import usb_midi

from adafruit_debouncer import Debouncer
import winterbloom_smolmidi as smolmidi

import constants as c


# Utilities for code.py (not boot.py)


class PulsatingLED:
    def __init__(self, pin, *, min_duty_cycle=0x1000, max_duty_cycle=0xFFFF, frequency=60, debug=print):
        self._min_duty = max(min(min_duty_cycle, 0xFFFF), 0x0000)
        self._max_duty = max(min(max_duty_cycle, 0xFFFF), 0x0000)
        self._duty_delta = self._max_duty - self._min_duty
        self._pwm = pwmio.PWMOut(pin, frequency=frequency)
        self._period = self._pulsate_started = 0.0
        self._flash_while_pulsating = False
        self._debug = debug
        self.state = "off"

    def solid(self, on=True):
        self._period = 0
        self._flash_while_pulsating = False
        self._pwm.duty_cycle = 0xFFFF if on else 0x0000
        self.state = "on" if on else "off"
        self._debug(f"[led] Turned LED {self.state}")

    def pulsate(self, period, *, flash=False):
        self._flash_while_pulsating = flash
        self._period = period
        self._pulsate_started = time.monotonic()
        self.state = f"{'flash' if flash else 'pulsate'}/period={period:.2f}s"
        self._debug(f"[led] Set LED to {self.state} (duty cycle: 0x{self._min_duty:04x} <> 0x{self._max_duty:04X})")

    def update(self):
        if self._period > 0:
            current_time = time.monotonic()
            elapsed = (current_time - self._pulsate_started) % self._period
            half_period = self._period / 2
            fading_in = elapsed < half_period

            if self._flash_while_pulsating:
                duty = 0xFFFF if fading_in else 0x0000
            else:
                if fading_in:
                    duty = int(self._min_duty + self._duty_delta * (elapsed / half_period))
                else:
                    duty = int(self._max_duty - self._duty_delta * ((elapsed - half_period) / half_period))
            self._pwm.duty_cycle = duty


class SystemBase:
    def __init__(self, debug=print):
        self._debug = debug

    @staticmethod
    def msgpack_helper(type, obj):
        bytes_io = io.BytesIO()
        msgpack.pack((type, obj), bytes_io)
        return bytes_io.getvalue()

    def update(self):
        raise NotImplementedError()

    def send_obj(self, type, obj=None, *, skip_debug_msg=False, flush=False):
        raise NotImplementedError()

    def send_button_press(self, pressed):
        raise NotImplementedError()

    def send_reset_notification(self):
        raise NotImplementedError()

    def flush(self):
        self._write_outgoing(flush=True)

    def on_led_change(self, num):
        raise NotImplementedError()

    def on_system_reset(self):
        raise NotImplementedError()

    def on_ping(self):
        raise NotImplementedError()

    def on_stats(self):
        raise NotImplementedError()

    def on_simulate_press(self, pressed):
        raise NotImplementedError()

    def on_reset(self, flash):
        raise NotImplementedError()

    def on_next_boot_override(self, override):
        raise NotImplementedError()


class MIDISystemBase(SystemBase):
    def __init__(self, debug=print):
        super().__init__(debug=debug)
        self._outgoing = bytearray()
        self._midi_in = smolmidi.MidiIn(usb_midi.ports[0])
        self._midi_out = usb_midi.ports[1]

    def update(self):
        msg = self._midi_in.receive()
        if msg is not None:
            if msg.type == smolmidi.CC and msg.channel == 0 and msg.data[0] == c.MIDI_LED_CTRL:
                self.on_led_change(msg.data[1])

            elif msg.type == smolmidi.SYSTEM_RESET:
                self.on_system_reset()

            elif msg.type == smolmidi.SYSEX:
                msg, truncated = self._midi_in.receive_sysex(c.SYSEX_MAX_LEN)
                if truncated:
                    self._debug("[midi] WARNING: Truncated sysex message. Skipping!")
                elif msg.startswith(c.SYSEX_PREFIX):
                    self._on_sysex(msg[c.SYSEX_PREFIX_LEN :])
                elif len(msg) > 0:  # Ignore empty messages
                    self._debug("[midi] WARNING: Bad sysex message: %s" % msg)

            else:
                self._debug(f"[midi] WARNING: Unrecognized MIDI msg: {bytes(msg)}")

        self._write_outgoing()

    def send_midi_bytes(self, msg, flush=False):
        self._outgoing.extend(msg)
        if flush:
            self.flush()

    def send_button_press(self, pressed):
        self.send_midi_bytes((smolmidi.CC, c.MIDI_BTN_CTRL, c.BTN_PRESSED if pressed else c.BTN_RELEASED))

    def send_reset_notification(self):
        self.send_midi_bytes((smolmidi.SYSTEM_RESET,))

    def send_obj(self, type, obj=None, *, skip_debug_msg=False, flush=False):
        # Use msgpack to pack data as binary, then encode most significant bit of
        # following 7 bytes first as: 0b07654321 0b01111111 0b02222222 ... 0b07777777
        unpacked = self.msgpack_helper(type, obj)
        packed = bytearray(b"%c%s" % (smolmidi.SYSEX, c.SYSEX_PREFIX))  # MIDI SysEx prefix

        for index in range(0, len(unpacked), 7):
            chunk = unpacked[index : index + 7]  # Chunk of 7 bytes or less
            msb_byte = 0  # Most significant bit byte
            for chunk_index, byte in enumerate(chunk):
                msb_byte |= ((byte & 0x80) >> 7) << chunk_index  # Extract most significant bit and shift it as above
            packed.append(msb_byte)  # Insert MSB byte before the next chunk
            packed.extend(byte & 0x7F for byte in chunk)  # Remove most significant bit from chunk's bytes

        packed.append(smolmidi.SYSEX_END)  # MIDI SysEx suffix

        if not skip_debug_msg:
            self._debug(f"[midi] Sending {type} object (sysex) of {len(packed)} bytes")
        self.send_midi_bytes(packed, flush=flush)

    def _on_sysex(self, msg):
        if msg == b"ping":
            self.on_ping()
        elif msg == b"stats":
            self.on_stats()
        elif msg in (b"simulate/press", b"simulate/release"):
            pressed = msg.split(b"/")[1] == b"press"
            self.on_simulate_press(pressed=pressed)
        elif msg in (b"reset", b"~~~!fLaSh!~~~"):
            flash = msg == b"~~~!fLaSh!~~~"
            self.on_reset(flash=flash)
        elif msg in (b"next-boot/%s" % override for override in c.NEXT_BOOT_OVERRIDES):
            override = msg.split(b"/")[1].decode()
            self.on_next_boot_override(override=override)
        else:
            self._debug(f"[midi] WARNING: Unrecognized sysex message: {msg}")

    def _write_outgoing(self, *, flush=False):
        while len(self._outgoing) > 0:
            num_written = self._midi_out.write(self._outgoing)
            self._outgoing = self._outgoing[num_written:]  # Modify in place
            if not flush:
                break


class HIDSystemBase(SystemBase):
    def __init__(self, debug=print):
        super().__init__(debug=debug)
        self._device = usb_hid.devices[0]
        self._outgoing = []

    def update(self):
        for report_id in (c.LED_REPORT_ID, c.DATA_REQUEST_REPORT_ID):
            msg = self._device.get_last_received_report(report_id)
            if msg is not None:
                if report_id == c.LED_REPORT_ID:
                    self.on_led_change(msg[0])
                else:  # c.DATA_REQUEST_REPORT_ID
                    self._on_data_request(msg[0])

        self._write_outgoing()

    def send_button_press(self, pressed):
        self._device.send_report(b"%c" % (c.BTN_PRESSED if pressed else c.BTN_RELEASED), c.BUTTON_REPORT_ID)

    def send_reset_notification(self):
        self.send_obj("reset")

    def send_obj(self, type, obj=None, *, skip_debug_msg=False, flush=False):
        packed = self.msgpack_helper(type, obj)
        outgoing = []

        # Send size (unsigned short) and 0-right padded packed bytes
        size = len(packed)
        size_bytes = struct.pack("<H", size)
        first_msg_len = c.DATA_RESPONSE_REPORT_LENGTH - len(size_bytes)
        report, packed = packed[:first_msg_len], packed[first_msg_len:]
        outgoing.append(size_bytes + report + b"\x00" * (first_msg_len - len(report)))

        while len(packed) > 0:
            # Send more 0-right padded packed bytes (if required)
            report, packed = packed[: c.DATA_RESPONSE_REPORT_LENGTH], packed[c.DATA_RESPONSE_REPORT_LENGTH :]
            outgoing.append(report + b"\x00" * (c.DATA_RESPONSE_REPORT_LENGTH - len(report)))
        if not skip_debug_msg:
            self._debug(f"[hid] Sending {type} object of {size} bytes in {len(outgoing)} HID report(s)")
        self._outgoing.extend(outgoing)
        if flush:
            self.flush()

    def _on_data_request(self, cmd):
        if cmd == c.DATA_REQUEST_PING:
            self.on_ping()
        elif cmd == c.DATA_REQUEST_STATS:
            self.on_stats()
        elif cmd in (c.DATA_REQUEST_SIMULATE_PRESS, c.DATA_REQUEST_SIMULATE_RELEASE):
            pressed = cmd == c.DATA_REQUEST_SIMULATE_PRESS
            self.on_simulate_press(pressed=pressed)
        elif cmd == c.DATA_REQUEST_RESTART:
            self.on_system_reset()
        elif cmd in (c.DATA_REQUEST_RESET, c.DATA_REQUEST_FLASH):
            flash = cmd == c.DATA_REQUEST_FLASH
            self.on_reset(flash=flash)
        elif c.DATA_REQUEST_NEXT_BOOT_OVERRIDE_START <= cmd <= c.DATA_REQUEST_NEXT_BOOT_OVERRIDE_END:
            override = c.NEXT_BOOT_OVERRIDES[cmd - c.DATA_REQUEST_NEXT_BOOT_OVERRIDE_START]
            self.on_next_boot_override(override=override)
        else:
            self._debug(f"[hid] WARNING: Unrecognized data request: {cmd}")

    def _write_outgoing(self, *, flush=False):
        while len(self._outgoing) > 0:
            report = self._outgoing.pop(0)
            self._device.send_report(report, c.DATA_RESPONSE_REPORT_ID)
            if not flush:
                break


class USBConnectedBase:
    def __init__(self):
        for _ in range(12):
            if supervisor.runtime.usb_connected:
                break
            time.sleep(0.25)

        if is_connected := supervisor.runtime.usb_connected:
            self.on_connect()
        else:
            self.on_disconnect()
        self._was_connected = is_connected

    def update(self):
        is_connected = supervisor.runtime.usb_connected
        if is_connected and not self._was_connected:
            self.on_connect()
        elif not is_connected and self._was_connected:
            self.on_disconnect()
        self._was_connected = is_connected

    def on_connect(self):
        raise NotImplementedError()

    def on_disconnect(self):
        raise NotImplementedError()


class ButtonBase:
    def __init__(self, pin):
        button = digitalio.DigitalInOut(pin)
        button.pull = digitalio.Pull.UP
        self._button = Debouncer(button)

        self._builtin_led = digitalio.DigitalInOut(board.LED)
        self._builtin_led.direction = digitalio.Direction.OUTPUT

    @property
    def is_pressed(self):
        return self._button.value

    def update(self):
        self._button.update()
        if self._button.fell:
            self._builtin_led.value = True
            self.on_press(pressed=True)
        if self._button.rose:
            self._builtin_led.value = False
            self.on_press(pressed=False)

    def on_press(self, pressed):
        raise NotImplementedError()

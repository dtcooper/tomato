import digitalio
import io
import keypad
import msgpack
import pwmio
import supervisor
import time
import usb_midi

import winterbloom_smolmidi as smolmidi

from config import Config
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
        self._debug(f"Turned LED {self.state}")

    def pulsate(self, period, *, flash=False):
        self._flash_while_pulsating = flash
        self._period = period
        self._pulsate_started = time.monotonic()
        self.state = f"{'flash' if flash else 'pulsate'}/period={period:.2f}s"
        log_line = f"Set LED to {self.state}"
        if not flash:
            log_line = f"{log_line} (duty cycle: 0x{self._min_duty:04x} <> 0x{self._max_duty:04X})"
        self._debug(log_line)

    def update(self):
        if self._period > 0:
            current_time = time.monotonic()
            elapsed = (current_time - self._pulsate_started) % self._period
            half_period = self._period / 2
            fading_out = elapsed < half_period

            if self._flash_while_pulsating:
                duty = 0xFFFF if fading_out else 0x0000
            else:
                if fading_out:
                    duty = 0xFFFF - int(self._min_duty + self._duty_delta * (elapsed / half_period))
                else:
                    duty = 0xFFFF - int(self._max_duty - self._duty_delta * ((elapsed - half_period) / half_period))
            self._pwm.duty_cycle = duty


class MIDISystemBase:
    def __init__(self, debug=print):
        self._outgoing = bytearray()
        self._midi_in = smolmidi.MidiIn(usb_midi.ports[0])
        self._midi_out = usb_midi.ports[1]
        self._debug = debug

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
                    self._debug("WARNING: Truncated sysex message. Skipping!")
                elif msg.startswith(c.SYSEX_PREFIX):
                    self._on_sysex(msg[c.SYSEX_PREFIX_LEN :])
                elif len(msg) > 0:  # Ignore empty messages
                    self._debug("WARNING: Bad sysex message: %s" % msg)

            else:
                self._debug(f"WARNING: Unrecognized MIDI msg: {bytes(msg)}")

        self._write_outgoing()

    def send_bytes(self, msg):
        self._outgoing.extend(msg)

    @staticmethod
    def _obj_to_msgpack_bytes(obj):
        bytes_io = io.BytesIO()
        msgpack.pack(obj, bytes_io)
        return bytes_io.getvalue()

    @staticmethod
    def _packed_bytes_for_7bit_sysex(unpacked):
        packed = bytearray(b"%c%s" % (smolmidi.SYSEX, c.SYSEX_PREFIX))  # MIDI SysEx prefix

        for index in range(0, len(unpacked), 7):
            chunk = unpacked[index : index + 7]  # Chunk of 7 bytes or less
            msb_byte = 0  # Most significant bit byte
            for chunk_index, byte in enumerate(chunk):
                msb_byte |= ((byte & 0x80) >> 7) << chunk_index  # Extract most significant bit and shift it as above
            packed.append(msb_byte)  # Insert MSB byte before the next chunk
            packed.extend(byte & 0x7F for byte in chunk)  # Remove most significant bit from chunk's bytes

        packed.append(smolmidi.SYSEX_END)  # MIDI SysEx suffix
        return packed

    def send_obj(self, type, obj=None, *, skip_debug_msg=False):
        # Use msgpack to pack data as binary, then encode most significant bit of
        # following 7 bytes first as: 0b07654321 0b01111111 0b02222222 ... 0b07777777
        unpacked = self._obj_to_msgpack_bytes((type, obj))
        packed = self._packed_bytes_for_7bit_sysex(unpacked)

        if not skip_debug_msg:
            self._debug(f"Sending {type} sysex of {len(packed)} bytes")
        self.send_bytes(packed)

    def flush(self):
        self._write_outgoing(flush=True)

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
        elif msg in (b"next-boot/%s" % override for override in Config.NEXT_BOOT_OVERRIDES):
            override = msg.split(b"/")[1].decode()
            self.on_next_boot_override(override=override)
        elif msg == b"~~~!TeSt-ExCePtIoN!~~~":
            self.on_test_exception()
        else:
            self._debug(f"WARNING: Unrecognized sysex message: {msg}")

    def _write_outgoing(self, flush=False):
        while len(self._outgoing) > 0:
            num_written = self._midi_out.write(self._outgoing)
            self._outgoing = self._outgoing[num_written:]  # Modify in place
            if not flush:
                break

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

    def on_test_exception(self):
        raise NotImplementedError()


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
    def __init__(self, pin, *, trigger_pin):
        self._keys = keypad.Keys((pin,), value_when_pressed=False, pull=True)
        self._event = keypad.Event()
        if trigger_pin:
            self._builtin_led = digitalio.DigitalInOut(trigger_pin)
            self._builtin_led.direction = digitalio.Direction.OUTPUT
        else:
            self._builtin_led = None
        self.is_pressed = False

    def update(self):
        if self._keys.events.get_into(self._event):
            self.is_pressed = self._event.pressed
            if self._builtin_led:
                self._builtin_led.value = self.is_pressed
            self.on_press(pressed=self.is_pressed)

    def on_press(self, pressed):
        raise NotImplementedError()

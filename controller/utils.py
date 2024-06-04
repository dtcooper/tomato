import io
import msgpack
import pwmio
import supervisor
import time

from constants import SYSEX_STATS_PREFIX


# Utilities for code.py (not boot.py)


class PulsatingLED:
    def __init__(self, pin, *, min_duty_cycle=0x1000, max_duty_cycle=0xFFFF, frequency=60, debug=None):
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
        if self._debug:
            self._debug(f"Turned LED {self.state}")

    def pulsate(self, period, *, flash=False):
        self._flash_while_pulsating = flash
        self._period = period
        self._pulsate_started = time.monotonic()
        self.state = f"{'flash' if flash else 'pulsate'}/period={period:.2f}s"
        if self._debug:
            self._debug(f"Set LED to {self.state} (duty cycle: 0x{self._min_duty:04x} <> 0x{self._max_duty:04X})")

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


def encode_stats_sysex(obj):
    # Use msgpack to pack data as binary, then
    # encode most significant bit of following 7 bytes first as 0b07654321 0b01111111 0b02222222 ... 0b07777777
    bytes_io = io.BytesIO()
    msgpack.pack(obj, bytes_io)
    unpacked = bytes_io.getvalue()
    packed = bytearray(SYSEX_STATS_PREFIX)

    for index in range(0, len(unpacked), 7):
        chunk = unpacked[index : index + 7]  # Chunk of 7 bytes
        msb_byte = 0
        for chunk_index, byte in enumerate(chunk):
            msb_byte |= ((byte & 0x80) >> 7) << chunk_index  # Extract most significant bit and shift it as above
        packed.append(msb_byte)
        packed.extend(byte & 0x7F for byte in chunk)  # Remove most significant bit from chunk's bytes

    return bytes(packed)


class ConnectedBase:
    def __init__(self):
        for _ in range(12):
            if supervisor.runtime.usb_connected:
                break
            time.sleep(0.25)

        if is_connected := supervisor.runtime.usb_connected:
            self.on_connect()
        else:
            self.on_disconnect()
        self.was_connected = is_connected

    def update(self):
        is_connected = supervisor.runtime.usb_connected
        if is_connected and not self.was_connected:
            self.on_connect()
        elif not is_connected and self.was_connected:
            self.on_disconnect()
        self.was_connected = is_connected

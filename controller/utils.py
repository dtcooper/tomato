import io
import microcontroller
import msgpack
import pwmio
import time

from config import DEBUG
from constants import SYSEX_STATS_PREFIX


# Utilities for code.py (not boot.py)

BOOT_TIME = time.monotonic()
FORCED_DEBUG = microcontroller.nvm[1] == 1


def debug(s):
    if DEBUG or FORCED_DEBUG:
        print(f"t={time.monotonic() - BOOT_TIME:.03f} - {s}")


if FORCED_DEBUG:
    debug("Forcing DEBUG = True from nvm flag.")


class PulsatingLED:
    def __init__(self, pin, *, min_duty_cycle=0x1000, max_duty_cycle=0xFFFF, frequency=60):
        self._min_duty = max(min(min_duty_cycle, 0xFFFF), 0x0000)
        self._max_duty = max(min(max_duty_cycle, 0xFFFF), 0x0000)
        self._duty_delta = self._max_duty - self._min_duty
        self._pwm = pwmio.PWMOut(pin, frequency=frequency)
        self._period = self._pulsate_started = 0.0
        self._flash_while_pulsating = False
        self.state = "off"

    def solid(self, on=True):
        self._period = 0
        self._flash_while_pulsating = False
        self._pwm.duty_cycle = 0xFFFF if on else 0x0000
        self.state = "on" if on else "off"
        debug(f"Turned LED {self.state}")

    def pulsate(self, period, *, flash=False):
        debug(f"Set LED to pulsate, {period=}s (0x{self._min_duty:04x} <> 0x{self._max_duty:04X}), {flash=}")
        self._flash_while_pulsating = flash
        self._period = period
        self._pulsate_started = time.monotonic()
        self.state = f"{'flash' if flash else 'pulsate'}/period={period:.2f}s"

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
    bytes_io = io.BytesIO()
    msgpack.pack(obj, bytes_io)
    unpacked = bytes_io.getvalue()
    packed = bytearray(SYSEX_STATS_PREFIX)

    for index in range(0, len(unpacked), 7):
        chunk = unpacked[index : index + 7]
        msb_byte = 0
        for chunk_index, byte in enumerate(chunk):
            msb_byte |= ((byte & 0x80) >> 7) << chunk_index
        packed.append(msb_byte)
        packed.extend(byte & 0x7F for byte in chunk)

    return bytes(packed)


def uptime():
    return round(time.monotonic() - BOOT_TIME)

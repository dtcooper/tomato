import pwmio
import time

from config import DEBUG


class PulsatingLED:
    def __init__(self, pin, *, min_duty_cycle=0x1000, max_duty_cycle=0xFFFF, frequency=60):
        self._min_duty = max(min(min_duty_cycle, 0xFFFF), 0x0000)
        self._max_duty = max(min(max_duty_cycle, 0xFFFF), 0x0000)
        self._duty_delta = self._max_duty - self._min_duty
        self._pwm = pwmio.PWMOut(pin, frequency=frequency)
        self._period = self._pulsate_started = 0.0
        self._flash_while_pulsating = False

    def solid(self, on=True):
        self._period = 0
        self._flash_while_pulsating = False
        self._pwm.duty_cycle = 0xFFFF if on else 0x0000
        if DEBUG:
            print(f"Turned LED {'on' if on else 'off'}")

    def on(self):
        self.solid(on=True)

    def off(self):
        self.solid(on=False)

    def pulsate(self, period, *, flash=False):
        if DEBUG:
            print(f"Set LED to pulsate, {period=}s (0x{self._min_duty:04x} <> 0x{self._max_duty:04X}), {flash=}")
        self._flash_while_pulsating = flash
        self._period = period
        self._pulsate_started = time.monotonic()

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

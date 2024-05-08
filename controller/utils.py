import pwmio
import time

from config import DEBUG


class PulsatingLED:
    def __init__(self, pin, *, min_duty_cycle=0x2222, max_duty_cycle=0xFFFF, frequency=60):
        self._min_duty = max(min(min_duty_cycle, 0xFFFF), 0x0000)
        self._max_duty = max(min(max_duty_cycle, 0xFFFF), 0x0000)
        self._pwm = pwmio.PWMOut(pin, frequency=frequency)
        self._period = 0

    def solid(self, on=True):
        self._period = 0
        self._pwm.duty_cycle = 0xFFFF if on else 0x0000
        if DEBUG:
            print(f"Turned LED {'on' if on else 'off'}")

    def on(self):
        self.solid(on=True)

    def off(self):
        self.solid(on=False)

    def pulsate(self, period):
        if DEBUG:
            print(f"Set LED to pulsate with period of {period}s (0x{self._min_duty:04x} <> 0x{self._max_duty:04X})")
        self._period = period

    def update(self):
        if self._period > 0:
            current_time = time.monotonic()
            elapsed = current_time % self._period
            half_period = self._period / 2

            if elapsed < half_period:
                duty = int(self._min_duty + (self._max_duty - self._min_duty) * (elapsed / half_period))
            else:
                duty = int(self._max_duty - (self._max_duty - self._min_duty) * ((elapsed - half_period) / half_period))
            self._pwm.duty_cycle = duty

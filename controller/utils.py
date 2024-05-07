import board
import os
import pwmio
import time


def config_bool(name: str, default: bool = False) -> bool:
    return bool(os.getenv(name.upper(), default))


def config_gpio_pin(name):
    number = os.getenv(f"{name.upper()}_PIN")
    return getattr(board, f"GP{number}")


class PulsatingLED:
    def __init__(self, pin, min_duty_cycle=0x2222, max_duty_cycle=0xFFFF, frequency=60):
        self._min_duty = max(min(min_duty_cycle, 0xFFFF), 0x0000)
        self._max_duty = max(min(max_duty_cycle, 0xFFFF), 0x0000)
        self._pwm = pwmio.PWMOut(pin, frequency=frequency)
        self._period = 0

    def solid(self, on=True):
        self._period = 0
        self._pwm.duty_cycle = 0xFFFF if on else 0x0000
        print(f"Turned LED {'on' if on else 'off'}")

    def on(self):
        self.solid(on=True)

    def off(self):
        self.solid(on=False)

    def pulsate(self, period):
        print(f"Set LED to pulsate with period of {period}s (0x{self._min_duty:04x} <> 0x{self._max_duty:04X})")
        self._period = period

    def update(self):
        if self._period > 0:
            current_time = time.monotonic()
            elapsed_time = current_time % self._period
            half_period = self._period / 2

            if elapsed_time < half_period:
                duty_cycle = int(self._min_duty + (self._max_duty - self._min_duty) * (elapsed_time / half_period))
            else:
                duty_cycle = int(self._max_duty - (self._max_duty - self._min_duty) * ((elapsed_time - half_period) / half_period))
            self._pwm.duty_cycle = duty_cycle

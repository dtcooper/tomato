import board
import microcontroller
import os
import storage

import toml


SETTINGS_FILE = "settings.toml"
DEFAULT_SETTINGS_TOML = """\
### Pins ###
button = "GP17"  # Pin number for button
led = "GP16"  # Pin number for LED


### Debugging ###
# Debug mode, mounts drive and turns on serial console.
# Forced if button is pressed at boot time or on receipt of debug sysex MIDI message (see tester tool)
debug = false

# Debug messages get sent using MIDI sysex
debug_messages_over_transport = false

# Enable auto-reload on file changes when debug = True
autoreload = true


### LED ###
# Whether to flash LED when USB is disconnected
flash_on_usb_disconnect = true

# These defaults should be okay
pwm_min_duty_cycle = 0x0000
pwm_max_duty_cycle = 0xFFFF
pwm_frequency = 350

# In seconds
flash_period = 1.0
pulsate_period_slow = 2.25
pulsate_period_medium = 1.25
pulsate_period_fast = 0.6
"""


class Config:
    NEXT_BOOT_OVERRIDES = ("debug", "debug_messages_over_transport")
    PIN_ATTRS = ("button", "led")

    button: str
    buttin_pin: microcontroller.Pin
    led: str
    led_pin: microcontroller.Pin
    debug: bool
    debug_messages_over_transport: bool
    autoreload: bool
    flash_on_usb_disconnect: bool
    pwm_min_duty_cycle: int
    pwm_max_duty_cycle: int
    pwm_frequency: int
    flash_period: float
    pulsate_period_slow: float
    pulsate_period_medium: float
    pulsate_period_fast: float

    def __init__(self, *, from_boot=False):
        is_first_boot = False
        if from_boot:
            try:
                is_first_boot = os.stat(SETTINGS_FILE)[6] < 10  # Smaller than 10 bytes, we need a new one
            except OSError:
                is_first_boot = True

            if is_first_boot:
                print("Creating default settings.toml")
                storage.remount("/", readonly=False)
                with open(SETTINGS_FILE, "w") as f:
                    f.write(DEFAULT_SETTINGS_TOML)
                storage.remount("/", readonly=True)

        self._defaults = toml.loads(DEFAULT_SETTINGS_TOML)
        with open(SETTINGS_FILE, "r") as f:
            self._config = toml.load(f)

        boot_nvm_end = len(self.NEXT_BOOT_OVERRIDES)
        code_nvm_end = 2 * len(self.NEXT_BOOT_OVERRIDES)
        if from_boot:
            if is_first_boot:
                microcontroller.nvm[0:code_nvm_end] = b"\x00" * code_nvm_end  # Clear out nvm on first boot
                print("Forcing config value debug = true (empty settings.toml, likely a first boot)")
                self.set_code_override_from_boot("debug", True)
            else:
                for index, override in enumerate(self.NEXT_BOOT_OVERRIDES):
                    if microcontroller.nvm[index]:
                        print(f"Forcing config value {override} = true (forced via nvm)")
                        self.set_code_override_from_boot(override, True)
                    else:
                        self.set_code_override_from_boot(override, False)
        else:
            override_values = microcontroller.nvm[boot_nvm_end : 2 * code_nvm_end]
            for override, value in zip(self.NEXT_BOOT_OVERRIDES, override_values):
                if value:
                    self._config[override] = True

        for pin_value in self.PIN_ATTRS:
            try:
                self._config.update({f"{pin}_pin": getattr(board, getattr(self, pin)) for pin in ("led", "button")})
            except AttributeError:
                raise Exception(f"{self._config[pin_value]} is an invalid pin value ({pin_value})")

    def set_next_boot_override_from_code(self, override, value=True):
        index = self.NEXT_BOOT_OVERRIDES.index(override)
        microcontroller.nvm[index] = 1 if value else 0

    def set_code_override_from_boot(self, override, value=True):
        index = self.NEXT_BOOT_OVERRIDES.index(override)
        code_index = index + len(self.NEXT_BOOT_OVERRIDES)
        if value:
            microcontroller.nvm[index] = 0  # Reset for next run
            microcontroller.nvm[code_index] = 1  # Set for code.py
            self._config[override] = True
        else:
            microcontroller.nvm[code_index] = 0  # Unset for code.py

    def __getattr__(self, attr):
        try:
            return self._config[attr]
        except KeyError:
            try:  # Try default if there's a miss
                return self._defaults[attr]
            except KeyError:
                raise Exception(f"Error getting config key: {attr}!")

    def keys(self):
        return filter(lambda k: not k.endswith("_pin"), set(self._config.keys()) | set(self._defaults.keys()))

    def items(self):
        return ((k, getattr(self, k)) for k in self.keys())

    def pretty(self):
        return {k: f"{v:.02f}" if isinstance(v, float) else v for k, v in self.items()}

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
sysex_debug_messages = false

# Enable auto-reload on file changes when debug = True
autoreload = true


### LED ###

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
    NEXT_BOOT_OVERRIDES = ("debug", "sysex_debug_messages")

    def __init__(self, *, from_boot=False, debug=print):
        self._debug = debug

        is_first_boot = False
        if from_boot:
            try:
                is_first_boot = os.stat(SETTINGS_FILE)[6] < 10  # Smaller than 10 bytes, we need a new one
            except OSError:
                is_first_boot = True

            if is_first_boot:
                self._debug("Creating default settings.toml")
                storage.remount("/", readonly=False)
                with open(SETTINGS_FILE, "w") as f:
                    f.write(DEFAULT_SETTINGS_TOML)
                storage.remount("/", readonly=True)

        with open(SETTINGS_FILE, "r") as f:
            self._config = toml.load(f)

        boot_nvm_end = len(self.NEXT_BOOT_OVERRIDES)
        code_nvm_end = 2 * len(self.NEXT_BOOT_OVERRIDES)
        if from_boot:
            if is_first_boot:
                microcontroller.nvm[0:code_nvm_end] = b"\x00" * code_nvm_end  # Clear out nvm on first boot
                self._debug("Forcing config value debug = true (empty settings.toml, likely a first boot)")
                self.set_code_override_from_boot("debug", True)
            else:
                for index, override in enumerate(self.NEXT_BOOT_OVERRIDES):
                    if microcontroller.nvm[index]:
                        self._debug(f"Forcing config value {override} = true (forced via nvm)")
                        self.set_code_override_from_boot(override, True)
                    else:
                        self.set_code_override_from_boot(override, False)
        else:
            override_values = microcontroller.nvm[boot_nvm_end : 2 * code_nvm_end]
            for override, value in zip(self.NEXT_BOOT_OVERRIDES, override_values):
                if value:
                    self._config[override] = True

    def set_next_boot_override_from_code(self, override, value=True):
        self._debug(f"Setting {override} = true for next boot")
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
            raise Exception(f"Error getting config key: {attr}!")

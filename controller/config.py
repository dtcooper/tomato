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
button_trigger_led = "LED"  # Pin number for button trigger LED (turned on when button is down) - false disables


### Debugging ###
# Debug mode, mounts drive and turns on serial console.
# Forced if button is pressed at boot time or on receipt of debug sysex MIDI message (see tester tool)
debug = false

# Debug messages get sent using MIDI sysex
debug_messages_over_midi = false

# Enable serial console (when debug = false ONLY, as it's always enabled when debug = true)
serial = false

# Enable auto-reload on file changes (when debug = true ONLY)
autoreload = true


### LED ###
# Whether to flash LED when USB is disconnected
flash_on_usb_disconnect = true

# These defaults should be okay
pulsate_min_brightness = 0  # Between 0 and 255
pulsate_max_brightness = 255  # Between 0 and 255

# In milliseconds
flash_period = 1000
pulsate_period_slow = 2250
pulsate_period_fast = 600
"""


class Config:
    NEXT_BOOT_OVERRIDES = ("debug", "debug_messages_over_midi", "serial")
    PIN_ATTRS = ("button", "led", "button_trigger_led")

    button: str
    button_pin: microcontroller.Pin
    led: str
    led_pin: microcontroller.Pin
    button_trigger_led: str | bool
    button_trigger_led_pin: microcontroller.Pin
    debug: bool
    debug_messages_over_midi: bool
    serial: bool
    autoreload: bool
    flash_on_usb_disconnect: bool
    pulsate_min_brightness: int
    pulsate_max_brightness: int
    flash_period: int
    pulsate_period_slow: int
    pulsate_period_fast: int

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
        try:
            with open(SETTINGS_FILE, "r") as f:
                self._config = toml.load(f)
        except Exception as e:
            import traceback

            traceback.print_exception(e)
            print("ERROR: Couldn't open settings.toml. Recovering from error by using defaults.")
            self._config = {}

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

        pin_attrs = list(self.PIN_ATTRS)
        if not self.button_trigger_led:
            pin_attrs.remove("button_trigger_led")
            self._config["button_trigger_led"] = self._config["button_trigger_led_pin"] = None

        try:
            self._config.update({f"{pin}_pin": getattr(board, getattr(self, pin)) for pin in pin_attrs})
        except Exception:
            print("Error setting pin value!")
            raise

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

    def to_dict(self):
        # <...>_pin keys don't exist in self._defaults
        return {k: getattr(self, k) for k in self._defaults.keys()}

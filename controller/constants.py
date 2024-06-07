# General
VERSION = "0.3.1"
PRODUCT_NAME = "Tomato Button Box"

# Kindly assigned by pid.codes (https://pid.codes/1209/7111/)
USB_VENDOR_ID = 0x1209
USB_PRODUCT_ID = 0x7111

# Button commands
MIDI_BTN_CTRL = 0x10
BTN_PRESSED = 0x7F
BTN_RELEASED = 0

# LED commands
MIDI_LED_CTRL = 0x11
LED_OFF = 0
LED_ON = 1
LED_FLASH = 2
LED_PULSATE_SLOW = 3
LED_PULSATE_MEDIUM = 4
LED_PULSATE_FAST = 5

# System Exclusive
SYSEX_NON_COMMERCIAL = 0x7D
SYSEX_PREFIX = b"%c!T~" % SYSEX_NON_COMMERCIAL  # 0x7D is the non-commercial sysex prefix
SYSEX_PREFIX_LEN = len(SYSEX_PREFIX)
SYSEX_STATS_PREFIX = b"S~"
SYSEX_MAX_LEN = 128
SYSEX_FLASH = b"~~~!fLaSh!~~~"

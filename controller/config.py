import board


# Configure pin numbers
BUTTON_PIN = board.GP17  # Pin number for button
LED_PIN = board.GP16  # Pin number for LED

# Debug mode, mounts drive and turns on serial console.
# Will be true if button is pressed or "debug" is sent via serial/MIDI command
DEBUG = False

# Enable auto-reload when DEBUG = True
AUTORELOAD = True

# Settings for LEDs (these defaults should be okay)
LED_PWM_MIN_DUTY_CYCLE = 0x0000
LED_PWM_MAX_DUTY_CYCLE = 0xFFFF
LED_PWM_FREQUENCY = 250

# in seconds
LED_FLASH_PERIOD = 1
LED_PULSATE_PERIOD_SLOW = 2.25
LED_PULSATE_PERIOD_MEDIUM = 1.25
LED_PULSATE_PERIOD_FAST = 0.6

import board


# Debug mode, mounts drive and turns on serial console.
# Will be true if button is pressed or "debug" is sent via serial/MIDI command
DEBUG = False

# Enable auto-reload when DEBUG = True
AUTORELOAD = True

# Pin number for button
BUTTON_PIN = board.GP15

# Pin number for LED
LED_PIN = board.GP22

# Brightness settings for LED (these defaults should be okay)
LED_PWM_MIN_DUTY_CYCLE = 0x1000
LED_PWM_MAX_DUTY_CYCLE = 0xFFFF
LED_PWM_FREQUENCY = 60

# Button Box Firmware

Here's the button box firmware for a Raspberry Pi Pico flashed with CircuitPython.

## Installation

1. Install [CircuitPython v9.1](https://circuitpython.org/board/raspberry_pi_pico/)
   or greater onto your Pi Pico
2. In the `lib/` folder on your device copy the following,
   [CircuitPython Libraries](https://circuitpython.org/libraries),
    - [`adafruit_ticks`](https://docs.circuitpython.org/projects/ticks/) (required for `adafruit_debouncer`)
    - [`adafruit_debouncer`](https://docs.circuitpython.org/projects/debouncer/)
    - [`adafruit_midi`](https://docs.circuitpython.org/projects/midi/)
3. Copy python (`*.py`) files and `settings.toml` in this folder on to your device

## Configuration

Edit `settings.toml`,

```
ENABLE_DEBUG = 0  # Debug mode, mounts drive and turns on serial console.
BUTTON_PIN = 15  # GPIO pin number for button
LED_PIN = 22  # GPIO pin number for LED
```

Note: when turning device on, if the button is pressed then `ENABLE_DEBUG` will
be set to ON regardless of value in `settings.toml`.

## Debugging Tools

1. [Google Labs web serial tester](https://googlechromelabs.github.io/serial-terminal/)
2. [WebMIDI tester](https://studiocode.dev/webmidi-tester/)

# Button Box Firmware

Here's the button box firmware for a Raspberry Pi Pico flashed with CircuitPython.

## Installation

1. Install [CircuitPython v9.1](https://circuitpython.org/board/raspberry_pi_pico/)
   or greater onto your Pi Pico
2. In the `lib/` folder on your device copy the following,
   [CircuitPython Libraries](https://circuitpython.org/libraries),
    - [`adafruit_ticks`](https://docs.circuitpython.org/projects/ticks/) (required for `adafruit_debouncer`)
    - [`adafruit_debouncer`](https://docs.circuitpython.org/projects/debouncer/)
    - [`winterbloom_smolmidi`](https://github.com/wntrblm/Winterbloom_SmolMIDI/)
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

## Basic MIDI Protocol

### Button Presses (Receive from Device)

Receive from the device **change control on channel 1** (`0xB0`) with purpose
byte **general purpose #1** (`0x10`) with a value as defined below to register
button presses,

| Bytes                           | Button Press State |
|---------------------------------|--------------------|
| <code>0xB0 0x10 **0x7F**</code> | **Pressed**        |
| <code>0xB0 0x10 **0x00**</code> | **Released**       |

### LED Control (Send to Device)

Send to the device **change control on channel 1** (`0xB0`) with purpose byte
**general purpose #2** (`0x11`) with a value as defined below to achieve the
following LED control actions,

| Bytes                           | LED Control Action                         |
|---------------------------------|--------------------------------------------|
| <code>0xB0 0x11 **0x00**</code> | **OFF**                                    |
| <code>0xB0 0x11 **0x01**</code> | **ON** (solid)                             |
| <code>0xB0 0x11 **0x02**</code> | **Pulsate SLOW** (period = 2.25 seconds)   |
| <code>0xB0 0x11 **0x03**</code> | **Pulsate MEDIUM** (period = 1.25 seconds) |
| <code>0xB0 0x11 **0x04**</code> | **Pulsate FAST** (period = 0.6 seconds)    |
| <code>0xB0 0x11 **0x05**</code> | **Flash** (period = 1.0 seconds)           |

## Debugging Tools

1. [Google Labs web serial tester](https://googlechromelabs.github.io/serial-terminal/)
2. [WebMIDI tester](https://studiocode.dev/webmidi-tester/)

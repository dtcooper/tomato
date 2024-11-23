# MIDI Controller - Button Box Firmware

Here's the MIDI controller button box firmware for a Raspberry Pi Pico flashed
with CircuitPython.

<div align="center">
  <img src="https://raw.github.com/dtcooper/tomato/main/.github/tomato-controller.jpg" width="300">
</div>

## Firmware Installation

1. Install [CircuitPython v9.1](https://circuitpython.org/board/raspberry_pi_pico/)
   or greater onto your Pi Pico.
2. In the `lib/` folder on your device copy the following,
   [CircuitPython Libraries](https://circuitpython.org/libraries),

    1. [`circuitpython_toml`](https://github.com/elpekenin/circuitpython_toml/)
    2. [`jled-circuitpython`](https://github.com/jandelgado/jled-circuitpython)
    3. [`winterbloom_smolmidi`](https://github.com/wntrblm/Winterbloom_SmolMIDI/)
       (optionally compile with
       [`mpy-cross`](https://adafruit-circuit-python.s3.amazonaws.com/index.html?prefix=bin/mpy-cross/))

    You can install the first and second dependencies (not `winterbloom_smolmidi`)
    using the [`circup`](https://github.com/adafruit/circup) tool,
    ```
    circup install jled toml
    ```

3. Copy all python (`*.py`) files in this folder on to your device.
4. Reset the device. Upon first boot, you'll see the `TOMATOBOX` drive, and
   you can edit the newly generated `settings.toml` file to your liking.

**NOTE:** After resetting the device again, the `TOMATOBOX` drive will disappear.
To boot the device into "debug" mode (and display the drive again), use the
testing tool linked in the [Development](#development) section of this document.

## Configuration

Edit `settings.toml` and set the button and led pins to match your setup.

```toml
### Pins ###
button = "GP17"  # Pin number for button
led = "GP16"  # Pin number for LED
```

For additional settings, see `settings.toml` generated after you first install
and reset your device.

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
| <code>0xB0 0x11 **0x02**</code> | **Flash** (period = 1.0 seconds)           |
| <code>0xB0 0x11 **0x03**</code> | **Pulsate SLOW** (period = 2.25 seconds)   |
| <code>0xB0 0x11 **0x04**</code> | **Pulsate FAST** (period = 0.6 seconds)    |

_**NOTE:** The device will acknowledge a correctly processed LED control change by
returning same message back. For example sending <code>0xB0 0x11 **0x01**</code> to
turn the LED on (solid) will receive <code>0xB0 0x11 **0x01**</code> back, which can be used
to confirm the LED has been turned on (solid)._

### Restart

To restart the device's program, send it the **system reset** byte (`0xFF`). The device
will send back a `0xFF` when it resets or starts up.

## Development

Use the files contained in the `test/` directory to test. (This is known to work in Google Chrome.)

## Circuit Diagram

<div align="center">
  <img src="https://raw.github.com/dtcooper/tomato/main/.github/tomato-controller-circuit.svg" width="400">
</div>

## Add'l Debugging Tools

1. [Google Labs web serial tester](https://googlechromelabs.github.io/serial-terminal/)
2. [WebMIDI tester](https://studiocode.dev/webmidi-tester/)

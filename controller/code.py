from adafruit_debouncer import Debouncer
import adafruit_midi
from adafruit_midi.control_change import ControlChange
import board
import digitalio
import microcontroller
import pwmio
import re
import supervisor
import time
import usb_midi

from utils import config_gpio_pin


BUTTON_CTRL = 0x10
LED_CTRL = 0x11
PRESSED = 0x7F
RELEASED = 0
OFF = 0
ON = 1
PULSATE_PERIODS = (2.5, 1.75, 1.0, 0.6, 0.4, 0.25, 0.175)
PULSATE_RANGE_START = 2
PULSATE_RANGE_END = 2 + len(PULSATE_PERIODS) - 1

CMD_LED_RE = re.compile(r"^led (\d+)$")
CMD_PRESS_RE = re.compile(r"^press(\s+(on|off))?")

print("Configuring pins")
button = digitalio.DigitalInOut(config_gpio_pin("button"))
button.pull = digitalio.Pull.UP
button = Debouncer(button)

led = pwmio.PWMOut(config_gpio_pin("led"), frequency=60)
pulsate_period = 0

builtin_led = digitalio.DigitalInOut(board.LED)
builtin_led.direction = digitalio.Direction.OUTPUT

print("Initializing MIDI")
midi = adafruit_midi.MIDI(
    midi_in=usb_midi.ports[0],
    in_channel=0,
    midi_out=usb_midi.ports[1],
    out_channel=0,
)


def set_led_solid(value=True):
    global pulsate_period
    led.duty_cycle = 0xFFFF if value else 0x0000
    pulsate_period = 0
    print(f"Turned LED {'on' if value else 'off'}")


def set_led_pulsate(period):
    global pulsate_period
    pulsate_period = period
    print(f"Set LED to pulsate with period of {period}s")


def pulsate_update():
    if pulsate_period > 0:
        current_time = time.monotonic()
        elapsed_time = current_time % pulsate_period
        half_period = pulsate_period / 2

        if elapsed_time < half_period:
            led.duty_cycle = int(0xFFFF * (elapsed_time / half_period))
        else:
            led.duty_cycle = int(0xFFFF - 0xFFFF * ((elapsed_time - half_period) / half_period))


def process_led_command(num):
    print(f"Received LED control message: {num}")
    if num in (ON, OFF):
        set_led_solid(num == ON)
    elif PULSATE_RANGE_START <= num <= PULSATE_RANGE_END:
        period = PULSATE_PERIODS[num - PULSATE_RANGE_START]
        set_led_pulsate(period=period)
    else:
        print(f"WARNING: Unrecognized LED control message: {num}")


def process_keypress(on=True):
    if on:
        midi.send(ControlChange(BUTTON_CTRL, PRESSED))
        print("Sending button pressed MIDI message")
        set_led_solid(False)
        builtin_led.value = True
    else:
        midi.send(ControlChange(BUTTON_CTRL, RELEASED))
        print("Sending button released MIDI message")
        builtin_led.value = False


print("Running main loop...\n")
while True:
    if supervisor.runtime.serial_bytes_available:
        cmd = input().strip().lower()
        if match := CMD_LED_RE.match(cmd):
            num = int(match.group(1))
            process_led_command(num)
        elif match := CMD_PRESS_RE.match(cmd):
            action = match.group(2)
            if action == "on":
                process_keypress(on=True)
            elif action == "off":
                process_keypress(on=False)
            else:
                process_keypress(on=True)
                time.sleep(0.1)
                process_keypress(on=False)
        elif cmd == "reset":
            print("Resetting...")
            microcontroller.reset()
        else:
            print("Invalid command. Usage:")
            print(" * led <digit>")
            print(" * press [ON | OFF]")
            print(" * reset")

    button.update()
    if button.fell:
        process_keypress(on=True)

    if button.rose:
        process_keypress(on=False)

    msg = midi.receive()
    if msg is not None and isinstance(msg, ControlChange):
        if msg.control == LED_CTRL:
            process_led_command(msg.value)
        else:
            print(f"WARNING: Unrecognized control message: {hex(msg.control)} / {hex(msg.value)}")

    pulsate_update()

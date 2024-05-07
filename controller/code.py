from adafruit_debouncer import Debouncer
from adafruit_midi.control_change import ControlChange
import adafruit_midi
import board
import digitalio
import pwmio
import time
import usb_midi

from utils import config_gpio_pin


BUTTON_CTRL = 0x10
LED_CTRL = 0x11
PRESSED = 0x7F
RELEASED = 0
OFF = 0
ON = 1
PULSATE_SLOW = 2
PULSATE_FAST = 3
PULSATE_SLOW_PERIOD = 2.5
PULSATE_FAST_PERIOD = 1

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


print("Running main loop...\n")
while True:
    button.update()
    if button.fell:
        midi.send(ControlChange(BUTTON_CTRL, PRESSED))
        print("Sending button pressed MIDI message")
        set_led_solid(False)
        builtin_led.value = True
    if button.rose:
        midi.send(ControlChange(BUTTON_CTRL, RELEASED))
        print("Sending button released MIDI message")
        builtin_led.value = False

    msg = midi.receive()
    if msg is not None and isinstance(msg, ControlChange):
        if msg.control == LED_CTRL:
            print("Received LED control message")
            if msg.value in (ON, OFF):
                set_led_solid(msg.value == ON)
            elif msg.value in (PULSATE_SLOW, PULSATE_FAST):
                set_led_pulsate(PULSATE_FAST_PERIOD if msg.value == PULSATE_FAST else PULSATE_SLOW_PERIOD)
            else:
                print(f"WARNING: Unrecognized LED control message: {msg.value}")
        else:
            print(f"WARNING: Unrecognized control message: {hex(msg.control)} / {hex(msg.value)}")

    pulsate_update()

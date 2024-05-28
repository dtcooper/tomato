from adafruit_debouncer import Debouncer
import board
import digitalio
import gc
import microcontroller
import supervisor
import time
import usb_midi
import winterbloom_smolmidi as midi

from common import __version__, LAST_MODIFIED, PRODUCT_NAME
from config import (
    BUTTON_PIN,
    DEBUG,
    LED_FLASH_PERIOD,
    LED_PIN,
    LED_PULSATE_PERIODS,
    LED_PWM_FREQUENCY,
    LED_PWM_MAX_DUTY_CYCLE,
    LED_PWM_MIN_DUTY_CYCLE,
)
from utils import b64_json_encode, debug, PulsatingLED, uptime


debug(f"Running {PRODUCT_NAME} v{__version__}. Last modified {LAST_MODIFIED}.")


# System Exclusive
SYSEX_PREFIX = b"\x7d!T~"  # 0x7D is the non-commercial sysex prefix
SYSEX_PREFIX_LEN = len(SYSEX_PREFIX)
SYSEX_MAX_LEN = 128

# Button commands
MIDI_BTN_CTRL = 0x10
BTN_PRESSED = 0x7F
BTN_RELEASED = 0

# LED commands
MIDI_LED_CTRL = 0x11
LED_OFF = 0
LED_ON = 1
LED_FLASH = 2
LED_PULSATE_RANGE_START = 3
LED_PULSATE_RANGE_END = LED_PULSATE_RANGE_START + len(LED_PULSATE_PERIODS) - 1


def do_keypress(on=True, *, midi_send_now=False):
    midi_send(b"%c%c%c" % (midi.CC, MIDI_BTN_CTRL, BTN_PRESSED if on else BTN_RELEASED), now=midi_send_now)
    if on:
        debug("Button pressed. Sending MIDI message.")
        builtin_led.value = True
    else:
        debug("Button released. Sending MIDI message.")
        builtin_led.value = False


def do_led_change(num):
    debug(f"Received LED control msg: {num}")
    if num in (LED_ON, LED_OFF):
        led.solid(num == LED_ON)
    elif num == LED_FLASH:
        led.pulsate(period=LED_FLASH_PERIOD, flash=True)
    elif LED_PULSATE_RANGE_START <= num <= LED_PULSATE_RANGE_END:
        period = LED_PULSATE_PERIODS[num - LED_PULSATE_RANGE_START]
        led.pulsate(period=period)
    else:
        debug(f"ERROR: Unrecognized LED control msg: {num}")
        send_sysex("error", f"Unrecognized LED control message: {num}")


def reset(*, mode=None):
    debug("Resetting...")
    if mode == "flash":
        debug("Next boot will be in UF2 mode")
        microcontroller.on_next_reset(microcontroller.RunMode.UF2)
    elif mode == "debug":
        debug("Next boot will force DEBUG = True")
        microcontroller.nvm[0] = 1
    else:
        mode = "regular"
    send_sysex(f"reset/{mode}", now=True)
    time.sleep(0.25)  # Wait for midi messages to go out
    microcontroller.reset()


def send_sysex(msg, *, now=False):
    midi_send(b"%c%s%s%c" % (midi.SYSEX, SYSEX_PREFIX, msg, midi.SYSEX_END), now=now)


def write_outgoing_midi_data():
    # Return False when there's nothing else to write
    while len(midi_outgoing_data) > 0:
        n = midi_out.write(midi_outgoing_data)
        debug(f"Wrote {n} bytes to midi")
        midi_outgoing_data[:] = midi_outgoing_data[n:]  # Modify in place
        return len(midi_outgoing_data) > 0
    return False


def midi_send(msg, *, now=False):
    midi_outgoing_data.extend(msg)
    if now:
        while write_outgoing_midi_data():
            pass


class ProcessUSBConnected:
    def __init__(self):
        self.usb_was_connected = True  # Assume we were connected, that way we'll process the transition

    def __call__(self):
        if supervisor.runtime.usb_connected:
            if not self.usb_was_connected:
                do_led_change(LED_OFF)
                send_sysex("connected")
                self.usb_was_connected = True
        elif self.usb_was_connected:
            do_led_change(LED_FLASH)
            self.usb_was_connected = False


def process_midi_sysex(msg):
    if msg == b"ping":
        send_sysex("pong")
    elif msg == b"stats":
        send_sysex(
            b"stats/%s"
            % b64_json_encode(
                {
                    "is-debug": DEBUG,
                    "led": led.state,
                    "mem-free": f"{gc.mem_free() / 1024:.1f}kB",
                    "modified": LAST_MODIFIED,
                    "pressed": not button.value,
                    "temp": f"{microcontroller.cpu.temperature:.2f}'C",
                    "uptime": uptime(),
                    "version": __version__,
                }
            )
        )
    elif msg.startswith(b"simulate-keypress"):
        if msg.endswith(b"/on"):
            do_keypress(on=True)
        elif msg.endswith(b"/off"):
            do_keypress(on=False)
        else:  # Full
            do_keypress(on=True, midi_send_now=True)
            time.sleep(0.125)
            do_keypress(on=False)
    elif msg == b"reset":
        reset()
    elif msg == b"!debug!":
        reset(mode="debug")
    elif msg == b"!flash!":
        reset(mode="flash")
    else:
        debug(f"Invalid sysex message: {msg}")


def process_midi():
    msg = midi_in.receive()
    if msg is not None:
        if msg.type == midi.CC and msg.channel == 0:
            do_led_change(msg.data[1])

        elif msg.type == midi.SYSEX:
            msg, truncated = midi_in.receive_sysex(SYSEX_MAX_LEN)
            if truncated:
                debug("WARNING: truncated sysex message. Skipping!")
            elif msg.startswith(SYSEX_PREFIX):
                process_midi_sysex(msg[len(SYSEX_PREFIX) :])

        else:
            debug(f"WARNING: Unrecognized MIDI msg: {bytes(msg)}")

    write_outgoing_midi_data()


def process_button():
    button.update()
    if button.fell:
        do_keypress(on=True)
    if button.rose:
        do_keypress(on=False)


process_usb_connected = ProcessUSBConnected()


debug("Configuring pins...")
button = digitalio.DigitalInOut(BUTTON_PIN)
button.pull = digitalio.Pull.UP
button = Debouncer(button)

led = PulsatingLED(
    LED_PIN,
    min_duty_cycle=LED_PWM_MIN_DUTY_CYCLE,
    max_duty_cycle=LED_PWM_MAX_DUTY_CYCLE,
    frequency=LED_PWM_FREQUENCY,
)

builtin_led = digitalio.DigitalInOut(board.LED)
builtin_led.direction = digitalio.Direction.OUTPUT

debug("Initializing MIDI...")
midi_in = midi.MidiIn(usb_midi.ports[0])
midi_out = usb_midi.ports[1]
midi_outgoing_data = bytearray()


while True:
    process_usb_connected()
    process_midi()
    process_button()
    led.update()

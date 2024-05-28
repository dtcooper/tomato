from adafruit_debouncer import Debouncer
import board
import digitalio
import gc
import microcontroller
import supervisor
import time
import usb_midi
import winterbloom_smolmidi as midi

from config import (
    BUTTON_PIN,
    DEBUG,
    LED_FLASH_PERIOD,
    LED_PIN,
    LED_PWM_FREQUENCY,
    LED_PWM_MAX_DUTY_CYCLE,
    LED_PWM_MIN_DUTY_CYCLE,
)
from constants import (
    BTN_PRESSED,
    BTN_RELEASED,
    LED_FLASH,
    LED_OFF,
    LED_ON,
    LED_PULSATE_PERIODS,
    LED_PULSATE_RANGE_END,
    LED_PULSATE_RANGE_START,
    MIDI_BTN_CTRL,
    MIDI_LED_CTRL,
    PRODUCT_NAME,
    SYSEX_CONNECTED_MSG,
    SYSEX_MAX_LEN,
    SYSEX_PREFIX,
    SYSEX_PREFIX_LEN,
    VERSION,
)
from utils import debug, encode_stats_sysex, PulsatingLED, uptime


debug(f"Running {PRODUCT_NAME} v{VERSION}.")


def do_keypress(on=True, *, now=False):
    send_midi_bytes(b"%c%c%c" % (midi.CC, MIDI_BTN_CTRL, BTN_PRESSED if on else BTN_RELEASED), now=now)
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


def send_sysex(msg, *, now=False, name=None):
    debug(f"Sending {msg if name is None else name} sysex")
    send_midi_bytes(b"%c%s%s%c" % (midi.SYSEX, SYSEX_PREFIX, msg, midi.SYSEX_END), now=now)


def write_outgoing_midi_data():
    # Return False when there's nothing else to write
    while len(midi_outgoing_data) > 0:
        n = midi_out.write(midi_outgoing_data)
        midi_outgoing_data[:] = midi_outgoing_data[n:]  # Modify in place
        return len(midi_outgoing_data) > 0
    return False


def send_midi_bytes(msg, *, now=False):
    midi_outgoing_data.extend(msg)
    if now:
        while write_outgoing_midi_data():
            pass


class ProcessUSBConnected:
    def __init__(self):
        if not supervisor.runtime.usb_connected:
            time.sleep(3)
        if supervisor.runtime.usb_connected:
            send_sysex(SYSEX_CONNECTED_MSG)
        self.usb_was_connected = True  # Always act like it was connected, so LEDs flashes if it's not

    def on_connect(self):
        do_led_change(LED_OFF)
        send_sysex(SYSEX_CONNECTED_MSG)

    def on_disconnect(self):
        do_led_change(LED_FLASH)

    def update(self):
        if supervisor.runtime.usb_connected:
            if not self.usb_was_connected:
                self.on_connect()
                self.usb_was_connected = True
        elif self.usb_was_connected:
            self.on_disconnect()
            self.usb_was_connected = False


def process_midi_sysex(msg):
    if msg == b"ping":
        send_sysex("pong")
    elif msg == b"stats":
        send_sysex(
            encode_stats_sysex(
                {
                    "is-debug": DEBUG,
                    "led": led.state,
                    "mem-free": f"{gc.mem_free() / 1024:.1f}kB",
                    "pressed": not button.value,
                    "temp": f"{microcontroller.cpu.temperature:.2f}'C",
                    "uptime": uptime(),
                    "version": VERSION,
                },
            ),
            name="stats",
        )
    elif msg.startswith(b"simulate-keypress"):
        if msg.endswith(b"/on"):
            do_keypress(on=True)
        elif msg.endswith(b"/off"):
            do_keypress(on=False)
        else:  # Full
            do_keypress(on=True, now=True)
            time.sleep(0.125)
            do_keypress(on=False)
        debug(f"Responded to {msg.decode()} sysex")
    elif msg == b"!debug!":
        reset(mode="debug")
    elif msg == b"!flash!":
        reset(mode="flash")
    else:
        debug(f"Invalid sysex message: {msg}")


def process_midi():
    msg = midi_in.receive()
    if msg is not None:
        if msg.type == midi.CC and msg.channel == 0 and msg.data[0] == MIDI_LED_CTRL:
            do_led_change(msg.data[1])

        elif msg.type == midi.SYSTEM_RESET:
            reset()

        elif msg.type == midi.SYSEX:
            msg, truncated = midi_in.receive_sysex(SYSEX_MAX_LEN)
            if truncated:
                debug("WARNING: truncated sysex message. Skipping!")
            elif msg.startswith(SYSEX_PREFIX):
                process_midi_sysex(msg[SYSEX_PREFIX_LEN:])

        else:
            debug(f"WARNING: Unrecognized MIDI msg: {bytes(msg)}")

    write_outgoing_midi_data()


def process_button():
    button.update()
    if button.fell:
        do_keypress(on=True)
    if button.rose:
        do_keypress(on=False)


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

process_usb_connected = ProcessUSBConnected()

while True:
    process_usb_connected.update()
    process_midi()
    process_button()
    led.update()

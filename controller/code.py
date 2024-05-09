from adafruit_debouncer import Debouncer
import board
import digitalio
import microcontroller
import re
import supervisor
import sys
import time
import usb_midi
import winterbloom_smolmidi as midi

from config import BUTTON_PIN, DEBUG, LED_PIN
from utils import PulsatingLED


if not DEBUG and microcontroller.nvm[1] == 1:
    DEBUG = True

OFF = 0
ON = 1
PULSATE_PERIODS = (1.75, 1, 0.6)
PULSATE_RANGE_START = 2
PULSATE_RANGE_END = 2 + len(PULSATE_PERIODS) - 1

SERIAL_COMMAND_LED_RE = re.compile(rb"^led (\d+)$")
SERIAL_COMMAND_PRESS_RE = re.compile(rb"^press(\s+(on|off))?")
SERIAL_COMMANDS = ("help", "led <digit>", "press [ON | OFF]", "uptime", "reset", "debug", "!flash!")

SYSEX_NON_COMMERCIAL = 0x7D
SYSEX_PREFIX = b"\x7dtomato:"
BUTTON_CTRL = 0x10
LED_CTRL = 0x11
PRESSED = 0x7F
RELEASED = 0


def debug(s):
    if DEBUG:
        print(s)


debug("Configuring pins")
button = digitalio.DigitalInOut(BUTTON_PIN)
button.pull = digitalio.Pull.UP
button = Debouncer(button)

led = PulsatingLED(LED_PIN)

builtin_led = digitalio.DigitalInOut(board.LED)
builtin_led.direction = digitalio.Direction.OUTPUT

debug("Initializing MIDI")
midi_in = midi.MidiIn(usb_midi.ports[0])
midi_out = usb_midi.ports[1]


def uptime():
    return time.monotonic() - boot_time


def do_led_change(num):
    debug(f"Received LED control msg: {num}")
    if num in (ON, OFF):
        led.solid(num == ON)
    elif PULSATE_RANGE_START <= num <= PULSATE_RANGE_END:
        period = PULSATE_PERIODS[num - PULSATE_RANGE_START]
        led.pulsate(period=period)
    else:
        debug(f"WARNING: Unrecognized LED control msg: {num}")
        send_tomato_sysex("bad-led-msg")


def do_keypress(on=True):
    midi_out.write(b"%c%c%c" % (midi.CC, BUTTON_CTRL, PRESSED if on else RELEASED))
    if on:
        debug("Sent button pressed MIDI msg")
        led.off()
        builtin_led.value = True
    else:
        debug("Sent button released MIDI msg")
        builtin_led.value = False


def reset(*, uf2_mode=False, debug_mode=False):
    debug("Resetting...")
    if uf2_mode:
        debug("Next boot will be in UF2 mode")
        microcontroller.on_next_reset(microcontroller.RunMode.UF2)
    if debug_mode:
        debug("Next boot will force DEBUG = True")
        microcontroller.nvm[0] = 1
    microcontroller.reset()


def process_serial():
    global serial_command

    if supervisor.runtime.serial_bytes_available:
        read = sys.stdin.read(1)
        serial_command += read
        sys.stdout.write(read)
        if serial_command.endswith("\n") or len(serial_command) >= 100:  # No need to store more than 100 chars
            serial_command = serial_command.strip().lower()
            if serial_command:
                if match := SERIAL_COMMAND_LED_RE.match(serial_command):
                    num = int(match.group(1))
                    do_led_change(num)
                elif match := SERIAL_COMMAND_PRESS_RE.match(serial_command):
                    action = match.group(2)
                    if action == "on":
                        do_keypress(on=True)
                    elif action == "off":
                        do_keypress(on=False)
                    else:
                        do_keypress(on=True)
                        time.sleep(0.1)
                        do_keypress(on=False)
                elif serial_command == "uptime":
                    debug(f"Uptime: {uptime():.5f}s")
                elif serial_command == "reset":
                    reset()
                elif serial_command == "debug":
                    reset(debug_mode=True)
                elif serial_command == "!flash!":
                    reset(uf2_mode=True)
                else:
                    if serial_command != "help":
                        debug(f"Invalid command: {serial_command}")
                    cmds = "\n * ".join(SERIAL_COMMANDS)
                    debug(f"Usage:\n * {cmds}")
            serial_command = ""


def process_button():
    button.update()
    if button.fell:
        do_keypress(on=True)
    if button.rose:
        do_keypress(on=False)


def send_tomato_sysex(msg):
    midi_out.write(b"%c%s%s%c" % (midi.SYSEX, SYSEX_PREFIX, msg, midi.SYSEX_END))


def process_midi():
    msg = midi_in.receive()
    if msg is not None:
        if msg.type == midi.CC and msg.channel == 0:
            if msg.data[0] == LED_CTRL:
                do_led_change(msg.data[1])
            else:
                debug(f"WARNING: Unrecognized ctrl MIDI msg: {bytes(msg)}")
                send_tomato_sysex("bad-ctrl-msg")

        elif msg.type == midi.SYSEX:
            cmd, _ = midi_in.receive_sysex(128)
            if cmd.startswith(SYSEX_PREFIX):
                cmd = cmd[len(SYSEX_PREFIX) :]
                if cmd == b"debug":
                    send_tomato_sysex("reset:debug")
                    reset(debug_mode=True)
                elif cmd == b"reset":
                    send_tomato_sysex("reset")
                    reset()
                elif cmd == b"!flash!":
                    send_tomato_sysex("reset:flash")
                    reset(uf2_mode=True)
                elif cmd == b"ping":
                    debug("Responding to ping sysex MIDI msg")
                    send_tomato_sysex(b"pong")
                elif cmd == b"uptime":
                    debug("Responding to uptime sys MIDI msg")
                    send_tomato_sysex(b"uptime:%.5fs" % uptime())
                else:
                    debug(f"WARNING: Unrecognized command MIDI msg: {cmd}")
                    send_tomato_sysex("bad-cmd-msg")
            else:
                debug(f"WARNING: Unrecognized sysex MIDI msg: {cmd}")
                send_tomato_sysex("bad-sysex-msg")

        else:
            debug(f"WARNING: Unrecognized MIDI msg: {bytes(msg)}")
            if DEBUG:
                send_tomato_sysex("bad-msg-debug")


boot_time = time.monotonic()
serial_command = ""
debug("Running main loop...\n")
send_tomato_sysex(b"starting")

while True:
    if DEBUG:
        process_serial()

    process_button()
    process_midi()
    led.update()

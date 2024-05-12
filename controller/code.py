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

from config import BUTTON_PIN, DEBUG, LED_PIN, LED_PWM_FREQUENCY, LED_PWM_MAX_DUTY_CYCLE, LED_PWM_MIN_DUTY_CYCLE
from utils import PRODUCT_NAME, PulsatingLED, __version__


if not DEBUG and microcontroller.nvm[1] == 1:
    DEBUG = True

# Button commands
MIDI_BTN_CTRL = 0x10
BTN_PRESSED = 0x7F
BTN_RELEASED = 0

# LED commands
MIDI_LED_CTRL = 0x11
LED_OFF = 0
LED_ON = 1
LED_PULSATE_PERIODS = (2.25, 1.25, 0.6)  # slow, medium, fast
LED_PULSATE_RANGE_START = 2
LED_PULSATE_RANGE_END = 2 + len(LED_PULSATE_PERIODS) - 1
LED_FLASH_PERIOD = 1
LED_FLASH = LED_PULSATE_RANGE_END + 1

# Serial
SERIAL_COMMAND_LED_RE = re.compile(rb"^led (\d+)$")
SERIAL_COMMAND_PRESS_RE = re.compile(rb"^press(\s+(on|off))?")
SERIAL_COMMANDS = ("help", "led <digit>", "press [ON | OFF]", "version", "ping", "uptime", "reset", "debug", "!flash!")

# Sysex prefix
SYSEX_NON_COMMERCIAL = 0x7D
SYSEX_PREFIX = b"%ctomato:" % SYSEX_NON_COMMERCIAL


def debug(s):
    if DEBUG:
        print(s)


debug(f"Running {PRODUCT_NAME} v{__version__}")


debug("Configuring pins")
button = digitalio.DigitalInOut(BUTTON_PIN)
button.pull = digitalio.Pull.UP
button = Debouncer(button)

led = PulsatingLED(
    LED_PIN,
    min_duty_cycle=LED_PWM_MIN_DUTY_CYCLE,
    max_duty_cycle=LED_PWM_MAX_DUTY_CYCLE,
    frequency=LED_PWM_FREQUENCY,
    debug=DEBUG,
)

builtin_led = digitalio.DigitalInOut(board.LED)
builtin_led.direction = digitalio.Direction.OUTPUT

debug("Initializing MIDI")
midi_in = midi.MidiIn(usb_midi.ports[0])
midi_out = usb_midi.ports[1]


def do_led_change(num):
    debug(f"Received LED control msg: {num}")
    if num in (LED_ON, LED_OFF):
        led.solid(num == LED_ON)
    elif LED_PULSATE_RANGE_START <= num <= LED_PULSATE_RANGE_END:
        period = LED_PULSATE_PERIODS[num - LED_PULSATE_RANGE_START]
        led.pulsate(period=period)
    elif num == LED_FLASH:
        led.pulsate(period=LED_FLASH_PERIOD, flash=True)
    else:
        debug(f"WARNING: Unrecognized LED control msg: {num}")
        send_tomato_sysex("bad-led-msg")


def do_keypress(on=True):
    midi_out.write(b"%c%c%c" % (midi.CC, MIDI_BTN_CTRL, BTN_PRESSED if on else BTN_RELEASED))
    if on:
        debug("Sent button pressed MIDI msg")
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


def process_cmd(cmd: bytes):  # None = error, False = no response
    if cmd == b"uptime":
        return b"%.5fs" % (time.monotonic() - boot_time)
    elif cmd == b"temp":
        return b"%.2f'C" % microcontroller.cpu.temperature
    elif cmd == b"ping":
        return b"pong"
    elif cmd == b"version":
        return "v%s" % __version__
    elif cmd == b"reset":
        send_tomato_sysex("reset")
        reset()
        return False
    elif cmd == b"debug":
        send_tomato_sysex("reset:debug")
        reset(debug_mode=True)
        return False
    elif cmd == b"!flash!":
        send_tomato_sysex("reset:flash")
        reset(uf2_mode=True)
        return False
    return None


def process_serial():
    global serial_command

    if supervisor.runtime.serial_bytes_available:
        read = sys.stdin.read(1)
        serial_command += read
        sys.stdout.write(read)
        if serial_command.endswith("\n") or len(serial_command) >= 100:  # No need to store more than 100 chars
            serial_command = serial_command.strip().lower()
            if serial_command:
                help = f"Usage:\n * {'\n * '.join(SERIAL_COMMANDS)}"
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
                elif serial_command == "help":
                    debug(help)
                else:
                    value = process_cmd(serial_command.encode()).decode()
                    if value is None:
                        debug(f"Invalid command: {serial_command}")
                        debug(help)
                    elif value:
                        debug(f"{serial_command}: {value}")
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
            if msg.data[0] == MIDI_LED_CTRL:
                do_led_change(msg.data[1])
            else:
                debug(f"WARNING: Unrecognized ctrl MIDI msg: {bytes(msg)}")
                send_tomato_sysex("bad-ctrl-msg")

        elif msg.type == midi.SYSEX:
            cmd, _ = midi_in.receive_sysex(128)
            if cmd.startswith(SYSEX_PREFIX):
                cmd = cmd[len(SYSEX_PREFIX):]
                value = process_cmd(cmd)
                if value is None:
                    debug(f"WARNING: Unrecognized command MIDI msg: {cmd.decode()}")
                    send_tomato_sysex("bad-cmd-msg")
                elif value:
                    debug(f"Responding to {cmd.decode()} sysex message")
                    send_tomato_sysex(b"%s:%s" % (bytes(cmd), value))
            else:
                debug(f"WARNING: Unrecognized sysex MIDI msg: {cmd}")
                send_tomato_sysex("bad-sysex-msg")

        else:
            debug(f"WARNING: Unrecognized MIDI msg: {bytes(msg)}")
            if DEBUG:
                send_tomato_sysex("bad-msg-debug")


boot_time = time.monotonic()
serial_command = ""

if usb_was_connected := supervisor.runtime.usb_connected:
    send_tomato_sysex(b"connected")
else:
    do_led_change(LED_FLASH)

debug("Running main loop...\n")
send_tomato_sysex(b"starting")


while True:
    if DEBUG:
        process_serial()

    if supervisor.runtime.usb_connected:
        if not usb_was_connected:
            do_led_change(LED_OFF)
            send_tomato_sysex(b"connected")
            usb_was_connected = True
    elif usb_was_connected:
        do_led_change(LED_FLASH)
        usb_was_connected = False

    process_button()
    process_midi()
    led.update()

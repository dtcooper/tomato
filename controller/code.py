from adafruit_debouncer import Debouncer
import board
import digitalio
import gc
import microcontroller
import pwmio
import re
import supervisor
import sys
import time
import usb_midi
import winterbloom_smolmidi as midi

from common import LAST_MODIFIED, PRODUCT_NAME, __version__
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
LED_FLASH = 2
LED_PULSATE_RANGE_START = 3
LED_PULSATE_RANGE_END = LED_PULSATE_RANGE_START + len(LED_PULSATE_PERIODS) - 1

# Serial
SERIAL_COMMAND_LED_RE = re.compile(rb"^led (\d+)$")
SERIAL_COMMAND_PRESS_RE = re.compile(rb"^press(\s+(on|off))?")
SERIAL_COMMANDS = (
    "help",
    "led <digit>",
    "press [ON | OFF]",
    "state",
    "is-debug",
    "version",
    "modified",
    "ping",
    "uptime",
    "stats",
    "reset",
    "!debug!",
    "!flash!",
)

# Sysex prefix
SYSEX_NON_COMMERCIAL = 0x7D
SYSEX_PREFIX = b"%ctomato:" % SYSEX_NON_COMMERCIAL


def debug(s):
    if DEBUG:
        print(s)


debug(f"Running {PRODUCT_NAME} v{__version__}. Last modified {LAST_MODIFIED}.")


class PulsatingLED:
    def __init__(self, pin, *, min_duty_cycle=0x1000, max_duty_cycle=0xFFFF, frequency=60):
        self._min_duty = max(min(min_duty_cycle, 0xFFFF), 0x0000)
        self._max_duty = max(min(max_duty_cycle, 0xFFFF), 0x0000)
        self._duty_delta = self._max_duty - self._min_duty
        self._pwm = pwmio.PWMOut(pin, frequency=frequency)
        self._period = self._pulsate_started = 0.0
        self._flash_while_pulsating = False

    def solid(self, on=True):
        self._period = 0
        self._flash_while_pulsating = False
        self._pwm.duty_cycle = 0xFFFF if on else 0x0000
        debug(f"Turned LED {'on' if on else 'off'}")

    def on(self):
        self.solid(on=True)

    def off(self):
        self.solid(on=False)

    def pulsate(self, period, *, flash=False):
        debug(f"Set LED to pulsate, {period=}s (0x{self._min_duty:04x} <> 0x{self._max_duty:04X}), {flash=}")
        self._flash_while_pulsating = flash
        self._period = period
        self._pulsate_started = time.monotonic()

    def update(self):
        if self._period > 0:
            current_time = time.monotonic()
            elapsed = (current_time - self._pulsate_started) % self._period
            half_period = self._period / 2
            fading_in = elapsed < half_period

            if self._flash_while_pulsating:
                duty = 0xFFFF if fading_in else 0x0000
            else:
                if fading_in:
                    duty = int(self._min_duty + self._duty_delta * (elapsed / half_period))
                else:
                    duty = int(self._max_duty - self._duty_delta * ((elapsed - half_period) / half_period))
            self._pwm.duty_cycle = duty


debug("Configuring pins")
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

debug("Initializing MIDI")
midi_in = midi.MidiIn(usb_midi.ports[0])
midi_out = usb_midi.ports[1]


led_state_global = b"off"


def do_led_change(num):
    global led_state_global

    debug(f"Received LED control msg: {num}")
    if num in (LED_ON, LED_OFF):
        led.solid(num == LED_ON)
        led_state_global = b"on" if num == LED_ON else b"off"
    elif num == LED_FLASH:
        led.pulsate(period=LED_FLASH_PERIOD, flash=True)
        led_state_global = b"flash"
    elif LED_PULSATE_RANGE_START <= num <= LED_PULSATE_RANGE_END:
        period = LED_PULSATE_PERIODS[num - LED_PULSATE_RANGE_START]
        led.pulsate(period=period)
        led_state_global = b"pulsate[%.2fs]" % period
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
    elif cmd == b"stats":
        return b"temp=%.2f'C/mem-free=%.1fkB" % (microcontroller.cpu.temperature, gc.mem_free() / 1024)
    elif cmd == b"ping":
        return b"pong"
    elif cmd == b"version":
        return b"v%s" % __version__
    elif cmd == b"modified":
        return LAST_MODIFIED.encode()
    elif cmd == b"is-debug":
        return b"on" if DEBUG else b"off"
    elif cmd == b"state":
        return b"led=%s/button=%s" % (led_state_global, b"released" if button.value else b"pressed")
    elif cmd == b"reset":
        send_tomato_sysex("reset")
        reset()
        return False
    elif cmd == b"!debug!":
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
                    value = process_cmd(serial_command.encode())
                    if value is None:
                        debug(f"Invalid command: {serial_command}")
                        debug(help)
                    elif value:
                        debug(f"{serial_command}: {value.decode()}")
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
                cmd = bytes(cmd[len(SYSEX_PREFIX) :])
                value = process_cmd(cmd)
                if value is None:
                    debug(f"WARNING: Unrecognized command MIDI msg: {cmd.decode()}")
                    send_tomato_sysex(b"bad-command:%s" % cmd)
                elif value:
                    debug(f"Responding to {cmd.decode()} sysex message")
                    send_tomato_sysex(b"%s:%s" % (cmd, value))
            else:
                debug(f"WARNING: Unrecognized sysex MIDI msg: {cmd.decode()}")

        else:
            debug(f"WARNING: Unrecognized MIDI msg: {bytes(msg)}")


boot_time = time.monotonic()
serial_command = ""

for first_try in (True, False):
    if usb_was_connected := supervisor.runtime.usb_connected:
        send_tomato_sysex(b"connected")
        break
    else:
        if first_try:  # Sleep on first try, to prevent LED flicker
            time.sleep(3)
        else:  # Otherwise "flash"
            do_led_change(LED_FLASH)

debug("Running main loop...\n")
debug("Sent MIDI reset msg")
midi_out.write(b"\xff")  # Device just reset
send_tomato_sysex(b"version:%s" % process_cmd(b"version"))
send_tomato_sysex(b"modified:%s" % process_cmd(b"modified"))


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

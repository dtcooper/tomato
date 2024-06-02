from adafruit_debouncer import Debouncer
import board
import digitalio
import gc
import microcontroller
import supervisor
import time
import usb_midi
import winterbloom_smolmidi as smolmidi

from config import Config
from constants import (
    BTN_PRESSED,
    BTN_RELEASED,
    LED_FLASH,
    LED_OFF,
    LED_ON,
    LED_PULSATE_RANGE_END,
    LED_PULSATE_RANGE_START,
    MIDI_BTN_CTRL,
    MIDI_LED_CTRL,
    PRODUCT_NAME,
    SYSEX_FLASH,
    SYSEX_MAX_LEN,
    SYSEX_PREFIX,
    SYSEX_PREFIX_LEN,
    VERSION,
)
from utils import encode_stats_sysex, PulsatingLED


config = Config()
BOOT_TIME = time.monotonic()
PULSATE_PERIODS = (config.pulsate_period_slow, config.pulsate_period_medium, config.pulsate_period_fast)


def debug(s):
    if config.debug or config.sysex_debug_messages:
        msg = f"t={time.monotonic() - BOOT_TIME:.03f} - {s}"
        if config.debug:
            print(msg)
        if config.sysex_debug_messages:
            send_sysex(b"debug/%s" % msg, skip_debug_msg=True)


def do_button_press(on=True):
    send_midi_bytes(b"%c%c%c" % (smolmidi.CC, MIDI_BTN_CTRL, BTN_PRESSED if on else BTN_RELEASED))
    if on:
        debug("Button pressed. Sending MIDI message.")
        builtin_led.value = True
    else:
        debug("Button released. Sending MIDI message.")
        builtin_led.value = False


def do_led_change(num):
    if num in (LED_ON, LED_OFF):
        led.solid(num == LED_ON)
    elif num == LED_FLASH:
        led.pulsate(period=config.flash_period, flash=True)
    elif LED_PULSATE_RANGE_START <= num <= LED_PULSATE_RANGE_END:
        period = PULSATE_PERIODS[num - LED_PULSATE_RANGE_START]
        led.pulsate(period=period)
    else:
        return False
    return True


def send_sysex(msg, *, name=None, skip_debug_msg=False):
    if all(0 <= b <= 0x7F for b in msg):
        if not skip_debug_msg:
            debug(f"Sending {msg.decode() if name is None else name} sysex")
        send_midi_bytes(b"%c%s%s%c" % (smolmidi.SYSEX, SYSEX_PREFIX, msg, smolmidi.SYSEX_END))
    else:
        debug("Attempted to send a sysex message that was out of range!")


def write_outgoing_midi_data(*, flush=False):
    # Return False when there's nothing else to write
    while len(midi_outgoing_data) > 0:
        n = midi_out.write(midi_outgoing_data)
        midi_outgoing_data[:] = midi_outgoing_data[n:]  # Modify in place
        if not flush:
            break


def send_midi_bytes(msg):
    midi_outgoing_data.extend(msg)


class ProcessUSBConnected:
    def __init__(self):
        for _ in range(12):
            if supervisor.runtime.usb_connected:
                break
            time.sleep(0.25)

        if is_connected := supervisor.runtime.usb_connected:
            self.on_connect()
        else:
            self.on_disconnect()
        self.was_connected = is_connected

    def on_connect(self):
        do_led_change(LED_OFF)
        msg = b"%s/%s%s" % (PRODUCT_NAME.lower().replace(" ", "-"), VERSION, b"/debug" if config.debug else b"")
        send_sysex(msg, name="connected")

    def on_disconnect(self):
        do_led_change(LED_FLASH)

    def update(self):
        is_connected = supervisor.runtime.usb_connected
        if is_connected and not self.was_connected:
            self.on_connect()
        elif not is_connected and self.was_connected:
            self.on_disconnect()
        self.was_connected = is_connected


def get_stats_dict():
    with open("boot_out.txt", "r") as f:
        boot_out = [line.strip() for line in f.readlines()]

    return {
        "boot-out": boot_out,
        "config": config.to_dict(),
        "led": led.state,
        "mem-free": f"{gc.mem_free() / 1024:.1f}kB",
        "pressed": not button.value,
        "temp": f"{microcontroller.cpu.temperature:.2f}'C",
        "uptime": round(time.monotonic() - BOOT_TIME),
        "version": VERSION,
    }


def process_midi_sysex(msg):
    if msg == b"ping":
        send_sysex(b"pong")
    elif msg == b"stats":
        msg = encode_stats_sysex(get_stats_dict())
        debug(f"Stats encoded into {len(msg)} sysex bytes")
        send_sysex(msg, name="stats")
    elif msg in (b"simulate/press", b"simulate/release"):
        action = msg.split(b"/")[1]
        debug(f"Simulating button {action.decode()}")
        do_button_press(on=action == b"press")
    elif msg in (b"reset", SYSEX_FLASH):
        if msg == SYSEX_FLASH:
            debug("Resetting into flash mode...")
            send_sysex(b"reset/flash")
            microcontroller.on_next_reset(microcontroller.RunMode.UF2)
        else:
            debug("Resetting...")
            send_sysex(b"reset")
        write_outgoing_midi_data(flush=True)
        time.sleep(0.25)  # Wait for midi messages to flush
        microcontroller.reset()
    elif msg in (b"next-boot/%s" % override for override in Config.NEXT_BOOT_OVERRIDES):
        override = msg.split(b"/")[1].decode()
        debug(f"Setting {override} = true for next boot")
        config.set_next_boot_override_from_code(override, True)
        send_sysex(b"next-boot/%s/true" % override)
    else:
        debug(f"WARNING: Unrecognized sysex message: {msg}")


def process_midi():
    msg = midi_in.receive()
    if msg is not None:
        if msg.type == smolmidi.CC and msg.channel == 0 and msg.data[0] == MIDI_LED_CTRL:
            num = msg.data[1]
            if do_led_change(num):
                debug(f"Received LED control msg: {num}")
                send_midi_bytes(b"%c%c%c" % (smolmidi.CC, MIDI_LED_CTRL, num))  # Acknowledge by sending bytes back
            else:
                debug(f"WARNING: Invalid LED control msg: {num}")
                send_sysex(b"invalid-led-ctrl/%d" % num)

        elif msg.type == smolmidi.SYSTEM_RESET:
            debug("Got system reset byte. Restarting.")
            send_midi_bytes((smolmidi.SYSTEM_RESET,))
            write_outgoing_midi_data(flush=True)
            time.sleep(0.1)  # Wait for midi messages to flush
            supervisor.reload()

        elif msg.type == smolmidi.SYSEX:
            msg, truncated = midi_in.receive_sysex(SYSEX_MAX_LEN)
            if truncated:
                debug("WARNING: Truncated sysex message. Skipping!")
            elif msg.startswith(SYSEX_PREFIX):
                process_midi_sysex(msg[SYSEX_PREFIX_LEN:])
            elif len(msg) > 0:  # Ignore empty messages
                debug("WARNING: Bad sysex message: %s" % msg)

        else:
            debug(f"WARNING: Unrecognized MIDI msg: {bytes(msg)}")

    write_outgoing_midi_data()


def process_button():
    button.update()
    if button.fell:
        do_button_press(on=True)
    if button.rose:
        do_button_press(on=False)


midi_outgoing_data = bytearray()


debug(f"Running {PRODUCT_NAME} v{VERSION}.")

debug("Configuring pins...")
button = digitalio.DigitalInOut(getattr(board, config.button))
button.pull = digitalio.Pull.UP
button = Debouncer(button)

led = PulsatingLED(
    getattr(board, config.led),
    min_duty_cycle=config.pwm_min_duty_cycle,
    max_duty_cycle=config.pwm_max_duty_cycle,
    frequency=config.pwm_frequency,
    debug=debug,
)

builtin_led = digitalio.DigitalInOut(board.LED)
builtin_led.direction = digitalio.Direction.OUTPUT

debug("Initializing MIDI...")
midi_in = smolmidi.MidiIn(usb_midi.ports[0])
midi_out = usb_midi.ports[1]

process_usb_connected = ProcessUSBConnected()

while True:
    process_usb_connected.update()
    process_midi()
    process_button()
    led.update()

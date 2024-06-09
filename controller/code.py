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
import constants as c
from utils import ConnectedBase, PulsatingLED, sysex_msgpack_7bit_encode


config = Config()
BOOT_TIME = time.monotonic()
PULSATE_PERIODS = {
    c.LED_PULSATE_SLOW: config.pulsate_period_slow,
    c.LED_PULSATE_MEDIUM: config.pulsate_period_medium,
    c.LED_PULSATE_FAST: config.pulsate_period_fast,
}


def debug(s):
    if config.debug or config.sysex_debug_messages:
        msg = f"t={time.monotonic() - BOOT_TIME:.03f} - {s}"
        if config.debug:
            print(msg)
        if config.sysex_debug_messages:
            send_sysex("debug", msg, skip_debug_msg=True)


def do_button_press(pressed=True):
    send_midi_bytes((smolmidi.CC, c.MIDI_BTN_CTRL, c.BTN_PRESSED if pressed else c.BTN_RELEASED))
    if pressed:
        debug("Button pressed. Sending MIDI message.")
        builtin_led.value = True
    else:
        debug("Button released. Sending MIDI message.")
        builtin_led.value = False


def do_led_change(num):
    if num in (c.LED_ON, c.LED_OFF):
        led.solid(num == c.LED_ON)
    elif num == c.LED_FLASH:
        led.pulsate(period=config.flash_period, flash=True)
    elif num in PULSATE_PERIODS:
        led.pulsate(period=PULSATE_PERIODS[num])
    else:
        return False
    return True


def write_outgoing_midi_data(*, flush=False):
    # Return False when there's nothing else to write
    while len(midi_outgoing_data) > 0:
        num_written = midi_out.write(midi_outgoing_data)
        midi_outgoing_data[:] = midi_outgoing_data[num_written:]  # Modify in place
        if not flush:
            break


def send_midi_bytes(msg, *, flush=False):
    midi_outgoing_data.extend(msg)
    if flush:
        write_outgoing_midi_data(flush=True)


def send_sysex(type, obj=None, *, skip_debug_msg=False, flush=False):
    msg = sysex_msgpack_7bit_encode(type, obj)
    if not skip_debug_msg:
        debug(f"Sending {type} sysex of {len(msg)} bytes")
    send_midi_bytes(msg, flush=flush)


class ProcessUSBConnected(ConnectedBase):
    def on_connect(self):
        debug("USB now in connected state. Sending reset byte and hello message.")
        do_led_change(c.LED_OFF)
        send_midi_bytes((smolmidi.SYSTEM_RESET,))
        send_sysex(
            "hello",
            "%s/%s%s" % (c.PRODUCT_NAME.lower().replace(" ", "-"), c.VERSION, "/debug" if config.debug else ""),
        )

    def on_disconnect(self):
        do_led_change(c.LED_FLASH)


def get_stats_dict():
    with open("boot_out.txt", "r") as f:
        boot_out = [line.strip() for line in f.readlines()]

    return {
        "boot-out": boot_out,
        "config": {key: getattr(config, key) for key in ("button", "led", "debug", "sysex_debug_messages")},
        "led": led.state,
        "mem-free": f"{gc.mem_free() / 1024:.1f}kB",
        "pressed": not button.value,
        "temp": f"{microcontroller.cpu.temperature:.2f}'C",
        "uptime": round(time.monotonic() - BOOT_TIME),
        "version": c.VERSION,
    }


def process_midi_sysex(msg):
    if msg == b"ping":
        send_sysex("pong")
    elif msg == b"stats":
        send_sysex("stats", get_stats_dict())
    elif msg in (b"simulate/press", b"simulate/release"):
        pressed = msg.split(b"/")[1] == b"press"
        debug(f"Simulating button {'press' if pressed else 'release'}")
        send_sysex("simulate", {"pressed": pressed})
        do_button_press(pressed=pressed)
    elif msg in (b"reset", b"~~~!fLaSh!~~~"):
        flash = msg == b"~~~!fLaSh!~~~"
        debug(f"Resetting{' into flash mode' if flash else ''}...")
        send_sysex("reset", {"flash": flash}, flush=True)
        if flash:
            microcontroller.on_next_reset(microcontroller.RunMode.UF2)
        time.sleep(0.25)  # Wait for midi messages to flush
        microcontroller.reset()
    elif msg in (b"next-boot/%s" % override for override in Config.NEXT_BOOT_OVERRIDES):
        override = msg.split(b"/")[1].decode()
        print(f"Setting {override} = true for next boot")
        config.set_next_boot_override_from_code(override, True)
        send_sysex("next-boot-override", {override: True})
    else:
        debug(f"WARNING: Unrecognized sysex message: {msg}")


def process_midi():
    msg = midi_in.receive()
    if msg is not None:
        if msg.type == smolmidi.CC and msg.channel == 0 and msg.data[0] == c.MIDI_LED_CTRL:
            num = msg.data[1]
            if do_led_change(num):
                debug(f"Received LED control msg: {num}")
                send_midi_bytes(b"%c%c%c" % (smolmidi.CC, c.MIDI_LED_CTRL, num))  # Acknowledge by sending bytes back
            else:
                debug(f"WARNING: Invalid LED control msg: {num}")
                send_sysex("error", f"Invalid MIDI control number {num}")

        elif msg.type == smolmidi.SYSTEM_RESET:
            debug("Got system reset byte. Restarting.")
            write_outgoing_midi_data(flush=True)
            time.sleep(0.1)  # Wait for midi messages to flush
            supervisor.reload()

        elif msg.type == smolmidi.SYSEX:
            msg, truncated = midi_in.receive_sysex(c.SYSEX_MAX_LEN)
            if truncated:
                debug("WARNING: Truncated sysex message. Skipping!")
            elif msg.startswith(c.SYSEX_PREFIX):
                process_midi_sysex(msg[c.SYSEX_PREFIX_LEN :])
            elif len(msg) > 0:  # Ignore empty messages
                debug("WARNING: Bad sysex message: %s" % msg)

        else:
            debug(f"WARNING: Unrecognized MIDI msg: {bytes(msg)}")

    write_outgoing_midi_data()


def process_button():
    button.update()
    if button.fell:
        do_button_press(pressed=True)
    if button.rose:
        do_button_press(pressed=False)


midi_outgoing_data = bytearray()


debug(f"Running {c.PRODUCT_NAME} v{c.VERSION}.")

debug("Configuring pins...")
button = digitalio.DigitalInOut(config.button_pin)
button.pull = digitalio.Pull.UP
button = Debouncer(button)

led = PulsatingLED(
    config.led_pin,
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

try:
    process_usb_connected = ProcessUSBConnected()

    while True:
        process_usb_connected.update()
        process_midi()
        process_button()
        led.update()

except Exception as e:
    import traceback

    for secs in range(5, 0, -1):
        error = f"An unexpected error occurred. Reloading in {secs}s...\n{'\n'.join(traceback.format_exception(e))}"
        debug(error)
        send_sysex("error", error, flush=True)
        time.sleep(1)

    supervisor.reload()

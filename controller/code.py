import gc
import microcontroller
import supervisor
import time

import winterbloom_smolmidi as smolmidi

from config import Config
import constants as c
from utils import ButtonBase, HIDSystemBase, MIDISystemBase, PulsatingLED, USBConnectedBase


config = Config()
BOOT_TIME = time.monotonic()
PULSATE_PERIODS = {
    c.LED_PULSATE_SLOW: config.pulsate_period_slow,
    c.LED_PULSATE_MEDIUM: config.pulsate_period_medium,
    c.LED_PULSATE_FAST: config.pulsate_period_fast,
}


def debug(s):
    if config.debug or config.debug_messages_over_transport:
        msg = f"t={time.monotonic() - BOOT_TIME:.03f} - {s}"
        if config.debug:
            print(msg)
        if config.debug_messages_over_transport:
            for device in devices:
                device.send_obj("debug", msg, skip_debug_msg=True)


class USBConnected(USBConnectedBase):
    def on_connect(self):
        debug("[usb] USB now in connected state. Sending reset byte and hello message.")
        led.solid(on=False)
        greeting = "%s/%s%s" % (c.PRODUCT_NAME.lower().replace(" ", "-"), c.VERSION, "/debug" if config.debug else "")
        for device in devices:
            device.send_reset_notification()
            device.send_obj("hello", greeting)

    def on_disconnect(self):
        led.pulsate(period=config.flash_period, flash=True)


class SystemMixin:
    name = None

    def on_led_change(self, num):
        if c.LED_RANGE_MIN <= num <= c.LED_RANGE_MAX:
            debug(f"[{self.name}] Received LED control msg: {num}")
            if isinstance(self, MIDISystemBase):  # Acknowledge by sending bytes back on MIDI only
                self.send_midi_bytes(b"%c%c%c" % (smolmidi.CC, c.MIDI_LED_CTRL, num))
            if num in (c.LED_ON, c.LED_OFF):
                led.solid(on=num == c.LED_ON)
            elif num == c.LED_FLASH:
                led.pulsate(period=config.flash_period, flash=True)
            elif num in PULSATE_PERIODS:
                led.pulsate(period=PULSATE_PERIODS[num])
        else:
            debug(f"[{self.name}] WARNING: Invalid LED control msg: {num}")
            self.send_obj("error", f"Invalid LED control number {num}")

    def on_system_reset(self):
        debug(f"[{self.name}] Got system reset byte. Restarting.")
        self.send_obj("reset", {"mode": "restart"}, flush=True)
        time.sleep(0.1)  # Wait for midi messages to flush
        supervisor.reload()

    def on_ping(self):
        self.send_obj("pong")

    def on_stats(self):
        with open("boot_out.txt", "r") as f:
            boot_out = [line.strip() for line in f.readlines()]
        self.send_obj(
            "stats",
            {
                "boot-out": boot_out,
                "config": config.pretty(),
                "led": led.state,
                "mem-free": f"{gc.mem_free() / 1024:.1f}kB",
                "pressed": not button.is_pressed,
                "temp": f"{microcontroller.cpu.temperature:.2f}'C",
                "uptime": round(time.monotonic() - BOOT_TIME),
                "version": c.VERSION,
            },
        )

    def on_simulate_press(self, pressed):
        debug(f"[{self.name}] Simulating button {'press' if pressed else 'release'}")
        self.send_obj("simulate", {"pressed": pressed})
        button.on_press(pressed=pressed)

    def on_reset(self, flash):
        debug(f"[{self.name}] Resetting{' into flash mode' if flash else ''}...")
        self.send_obj("reset", {"mode": "flash" if flash else "normal"}, flush=True)
        if flash:
            microcontroller.on_next_reset(microcontroller.RunMode.UF2)
        time.sleep(0.25)  # Wait for midi messages to flush
        microcontroller.reset()

    def on_next_boot_override(self, override):
        debug(f"[{self.name}] Setting {override} = true for next boot")
        config.set_next_boot_override_from_code(override, True)
        self.send_obj("next-boot-override", {override: True})

    def ack_led_change(self, num):
        raise NotImplementedError()


class MIDISystem(SystemMixin, MIDISystemBase):
    name = "midi"


class HIDSystem(SystemMixin, HIDSystemBase):
    name = "hid"


class Button(ButtonBase):
    def on_press(self, pressed):
        log_prefix = f"[button] Button {'pressed' if pressed else 'released'}."
        for device in devices:
            debug(f"{log_prefix} Sending {device.name.upper()} message.")
            device.send_button_press(pressed=pressed)


# These need to be defined before any calls to debug (calls midi.send_sysex)
midi = MIDISystem(debug=debug) if config.midi_transport else None
hid = HIDSystem(debug=debug) if config.hid_transport else None
devices = tuple(d for d in (midi, hid) if d is not None)

debug(f"Running {c.PRODUCT_NAME} v{c.VERSION}.")

debug(f"Configuring pins: button={config.button}, LED={config.led}...")
button = Button(pin=config.button_pin)
led = PulsatingLED(
    pin=config.led_pin,
    min_duty_cycle=config.pwm_min_duty_cycle,
    max_duty_cycle=config.pwm_max_duty_cycle,
    frequency=config.pwm_frequency,
    debug=debug,
)


try:
    usb = USBConnected()

    while True:
        usb.update()
        for device in devices:
            device.update()
        button.update()
        led.update()

except Exception as e:
    import traceback

    for secs in range(5, 0, -1):
        error = f"An unexpected error occurred. Reloading in {secs}s...\n{'\n'.join(traceback.format_exception(e))}"
        debug(error)
        for device in devices:
            device.send_obj("error", error, flush=True)
        time.sleep(1)

    supervisor.reload()

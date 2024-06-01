import board
import digitalio
import storage
import supervisor
import usb_cdc
import usb_hid
import usb_midi

from config import Config
from constants import PRODUCT_NAME, USB_PRODUCT_ID, USB_VENDOR_ID, VERSION


config = Config(from_boot=True)
usb_hid.disable()

MOUNT_NAME = "TOMATOBOX"

print(f"Booting {PRODUCT_NAME} v{VERSION}.")

supervisor.set_usb_identification(
    manufacturer="Tomato Radio Automation",
    product=PRODUCT_NAME,
    vid=USB_VENDOR_ID,
    pid=USB_PRODUCT_ID,
)
usb_midi.set_names(
    audio_control_interface_name=PRODUCT_NAME,
    in_jack_name="input",
    out_jack_name="output",
)

if not config.debug:
    button = digitalio.DigitalInOut(getattr(board, config.button))
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    if not button.value:
        print("Button pressed, running in debug mode")
        config.set_code_override_from_boot("debug", True)

mount = storage.getmount("/")
if mount.label != MOUNT_NAME:
    print(f"Renaming mount {mount.label} => {MOUNT_NAME}")
    storage.remount("/", readonly=False)
    mount.label = MOUNT_NAME
    storage.remount("/", readonly=True)

if config.debug:
    if not config.autoreload:
        print("Turning off autoreload")
        supervisor.runtime.autoreload = False
else:
    storage.disable_usb_drive()
    usb_cdc.disable()
    supervisor.runtime.autoreload = False

import digitalio
import microcontroller
import storage
import supervisor
import usb_cdc
import usb_hid
import usb_midi

from config import AUTORELOAD, BUTTON_PIN, DEBUG
from utils import PRODUCT_NAME, __version__


usb_hid.disable()

MOUNT_NAME = "TOMATOBOX"

print(f"Booting {PRODUCT_NAME} v{__version__}")

supervisor.set_usb_identification(
    manufacturer="Tomato Radio Automation",
    product=PRODUCT_NAME,
)
usb_midi.set_names(
    audio_control_interface_name=PRODUCT_NAME,
    in_jack_name="input",
    out_jack_name="output",
)

if DEBUG:
    print("Running in DEBUG mode")

if microcontroller.nvm[0] == 1:
    microcontroller.nvm[0:2] = b"\x00\x01"
    if not DEBUG:
        print("nvm flag set, running in DEBUG mode")
        DEBUG = True
else:
    microcontroller.nvm[1] = 0

if not DEBUG:
    button = digitalio.DigitalInOut(BUTTON_PIN)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    if not button.value:
        print("Button pressed, running in DEBUG mode")
        microcontroller.nvm[0:2] = b"\x00\x01"
        DEBUG = True

mount = storage.getmount("/")
if mount.label != MOUNT_NAME:
    print(f"Renaming mount {mount.label} => {MOUNT_NAME}")
    storage.remount("/", readonly=False)
    mount.label = MOUNT_NAME
    storage.remount("/", readonly=True)

if DEBUG:
    if not AUTORELOAD:
        print("Turning off autoreload")
        supervisor.runtime.autoreload = False
else:
    storage.disable_usb_drive()
    usb_cdc.disable()
    supervisor.runtime.autoreload = False

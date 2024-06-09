import digitalio
import storage
import supervisor
import usb_cdc
import usb_hid
import usb_midi

from config import Config
import constants as c


print(f"Booting {c.PRODUCT_NAME} v{c.VERSION} [{c.USB_VENDOR_ID:04x}:{c.USB_PRODUCT_ID:04x}]")
usb_hid.disable()

MOUNT_NAME = "TOMATOBOX"

supervisor.set_usb_identification(
    manufacturer="Tomato Radio Automation",
    product=c.PRODUCT_NAME,
    vid=c.USB_VENDOR_ID,
    pid=c.USB_PRODUCT_ID,
)
usb_midi.set_names(
    audio_control_interface_name=c.PRODUCT_NAME,
    in_jack_name="input",
    out_jack_name="output",
)

mount = storage.getmount("/")
if mount.label != MOUNT_NAME:
    print(f"Renaming mount {mount.label} => {MOUNT_NAME}")
    storage.remount("/", readonly=False)
    mount.label = MOUNT_NAME
    storage.remount("/", readonly=True)


config = Config(from_boot=True)
if not config.debug:
    button = digitalio.DigitalInOut(config.button_pin)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    if not button.value:
        print("Button pressed, running in debug mode")
        config.set_code_override_from_boot("debug", True)

if config.debug:
    if not config.autoreload:
        print("Turning off autoreload")
        supervisor.runtime.autoreload = False
else:
    storage.disable_usb_drive()
    usb_cdc.disable()
    supervisor.runtime.autoreload = False

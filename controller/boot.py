import digitalio
import microcontroller
import storage
import supervisor
import usb_cdc
import usb_hid
import usb_midi

from config import BUTTON_PIN, AUTORELOAD, DEBUG


usb_hid.disable()

product_name = "Tomato Button Box"
supervisor.set_usb_identification(
    manufacturer="Tomato Radio Automation",
    product=product_name,
)
usb_midi.set_names(
    audio_control_interface_name=product_name,
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

if DEBUG:
    if not AUTORELOAD:
        print("Turning off autoreload")
        supervisor.runtime.autoreload = False
else:
    storage.disable_usb_drive()
    usb_cdc.disable()
    supervisor.runtime.autoreload = False

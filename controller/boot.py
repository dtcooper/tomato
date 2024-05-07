import digitalio
import storage
import supervisor
import usb_cdc
import usb_hid
import usb_midi

from utils import config_bool, config_gpio_pin


usb_hid.disable()

supervisor.set_usb_identification(
    manufacturer="Tomato Radio Automation",
    product="Tomato Button Box",
)
usb_midi.set_names(
    streaming_interface_name="streaming interface",
    audio_control_interface_name="audio control",
    in_jack_name="in jack",
    out_jack_name="out jack",
)

debug = config_bool("enable_debug")

if not debug:
    button = digitalio.DigitalInOut(config_gpio_pin("button"))
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    debug = not button.value
    if debug:
        print("Forcing debug mode on (button pressed)")

if debug:
    print("Debug mode on")
else:
    storage.disable_usb_drive()
    usb_cdc.disable()

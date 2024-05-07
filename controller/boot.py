import digitalio
import microcontroller
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
        print("Forcing debug via button press")

if microcontroller.nvm and microcontroller.nvm[0] == 1:
    if not debug:
        debug = True
        print("Forcing debug via nvm")
    microcontroller.nvm[0] = 0  # Set to 0 for next boot

if debug:
    print("Running with debug mode on")
else:
    storage.disable_usb_drive()
    usb_cdc.disable()

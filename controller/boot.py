import digitalio
import storage
import supervisor
import usb_cdc
import usb_hid
import usb_midi

from config import Config
import constants as c


print(f"Booting {c.PRODUCT_NAME} v{c.VERSION} [{c.USB_VENDOR_ID:04x}:{c.USB_PRODUCT_ID:04x}]")
config = Config(from_boot=True)

MOUNT_NAME = "TOMATOBOX"

supervisor.set_usb_identification(
    manufacturer="Tomato Radio Automation",
    product=c.PRODUCT_NAME,
    vid=c.USB_VENDOR_ID,
    pid=c.USB_PRODUCT_ID,
)

if config.midi_transport:
    print("Enabling MIDI transport")
    usb_midi.set_names(
        audio_control_interface_name=c.PRODUCT_NAME,
        in_jack_name="input",
        out_jack_name="output",
    )
else:
    usb_midi.disable()

if config.hid_transport:
    print("Enabling HID transport")
    REPORTS = (
        (c.BUTTON_REPORT_ID, 1, True),
        (c.LED_REPORT_ID, 1, False),
        (c.DATA_REQUEST_REPORT_ID, 1, False),
        (c.DATA_RESPONSE_REPORT_ID, c.DATA_RESPONSE_REPORT_LENGTH, True),
    )
    raw_hid = usb_hid.Device(
        report_descriptor=(
            b"\x06\x00\xff\x09\x01\xa1\x01"
            + b"".join(
                b"\x85%c\x09\x00\x15\x00\x26\xff\x00\x75\x08\x95%c%c\x02\x01"
                % (report_id, size, 0x82 if sends else 0x92)
                for (report_id, size, sends) in REPORTS
            )
            + b"\xc0"
        ),
        usage_page=0xFF00,  # Vendor defined
        usage=0x01,  # Vendor page 1
        report_ids=tuple(report_id for report_id, _, _ in REPORTS),
        in_report_lengths=tuple(size if sends else 0 for _, size, sends in REPORTS),
        out_report_lengths=tuple(0 if sends else size for _, size, sends in REPORTS),
    )

    usb_hid.set_interface_name(c.PRODUCT_NAME)
    usb_hid.enable((raw_hid,))
else:
    usb_hid.disable()


mount = storage.getmount("/")
if mount.label != MOUNT_NAME:
    print(f"Renaming mount {mount.label} => {MOUNT_NAME}")
    storage.remount("/", readonly=False)
    mount.label = MOUNT_NAME
    storage.remount("/", readonly=True)


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

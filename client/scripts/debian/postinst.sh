#!/bin/sh

UDEV_FILE='50-elgato.rules'

# From https://github.com/julusian/node-elgato-stream-deck#linux
if [ -d '/etc/udev/rules.d/' ]; then
    echo 'Adding Elgato Stream Deck rules to udev ...'
    ln -fs "/usr/lib/tomato/${UDEV_FILE}" "/etc/udev/rules.d/${UDEV_FILE}"
    udevadm control --reload-rules
fi

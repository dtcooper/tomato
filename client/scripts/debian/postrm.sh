#!/bin/sh

UDEV_FILE='50-elgato.rules'

if [ -e /etc/udev/rules.d/50-elgato.rules ]; then
    echo 'Removing Elgato Stream Deck rules to udev ...'
    rm -f "/etc/udev/rules.d/${UDEV_FILE}"
    udevadm control --reload-rules
fi

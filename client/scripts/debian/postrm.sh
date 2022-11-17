#!/bin/sh

if [ -f /etc/udev/rules.d/50-elgato.rules ]; then
    echo 'Removing Elgato Stream Deck rules to udev ...'
    rm -f /etc/udev/rules.d/50-elgato.rules
    udevadm control --reload-rules
fi

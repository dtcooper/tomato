#!/bin/sh

if [ -f /etc/udev/rules.d/50-elgato.rules ]; then
    rm -f /etc/udev/rules.d/50-elgato.rules
    udevadm control --reload-rules
fi
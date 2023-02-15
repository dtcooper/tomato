#!/bin/sh

# From https://github.com/julusian/node-elgato-stream-deck#linux
if [ -d '/etc/udev/rules.d/' ]; then
    echo 'Adding Elgato Stream Deck rules to udev (reinsert Stream Deck to use) ...'
    ln -fs "/usr/lib/tomato/50-elgato.rules" "/etc/udev/rules.d/50-elgato.rules"
    udevadm control --reload-rules
else
    echo 'udev not found, not adding Elgato Stream Deck rules.'
fi

exit 0

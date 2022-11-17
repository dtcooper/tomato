#!/bin/sh

# Run locally for development
if [ "$npm_command" = 'run-script' ]; then
    CMD='electron-forge start --'
else
    CMD='/usr/lib/tomato/tomato'
fi

ARGS=
if [ "$XDG_SESSION_TYPE" = 'wayland' ]; then
    ARGS='--ozone-platform=wayland --enable-features=WaylandWindowDecorations'
fi

exec $CMD $ARGS $@
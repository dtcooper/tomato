#!/bin/sh

# Run locally for development
if [ "$npm_command" = 'run-script' ]; then
    CMD='electron-forge start'
    if [ "$DEV_EXTRA_FORGE_FLAGS" ]; then
        CMD="$CMD $DEV_EXTRA_FORGE_FLAGS"
    fi
    CMD="$CMD --"
# If we're running in an AppImage
elif [ "$APPIMAGE" ]; then
    CMD="$(dirname "$0")/tomato"
else
    CMD='/usr/lib/tomato/tomato'
fi

ARGS=
if [ "$XDG_SESSION_TYPE" = 'wayland' ]; then
    ARGS='--ozone-platform=wayland --enable-features=WaylandWindowDecorations'
fi

exec $CMD $ARGS $@

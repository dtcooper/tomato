#!/bin/bash


case "$OSTYPE" in
  msys)
    echo "windows"
    ;;

  linux*)
    echo "linux"
    ;;
  darwin*)
    if [ "$HOSTTYPE" = "x86_64" ]; then
        if [ "$MACOS_M1_EMULATED_BUILD" ]; then
            echo "macOS (M1 emulated)"
        else
            echo "macOS (x86-64)"
        fi
    else
        echo "macOS (M1)"
    fi
    ;;
  *)
    echo "Unknown OS: $OSTYPE"
    exit 1
    ;;
esac

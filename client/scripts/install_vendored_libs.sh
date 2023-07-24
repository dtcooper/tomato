#!/bin/sh

case "$OSTYPE" in
    darwin*)
        PLATFORM=darwin
        case "$(uname -m)" in
            x86_64) ARCH=x64 ;;
            arm64) ARCH=arm64 ;;
            *)
                echo 'Unknown macOS architecture.'
                exit 1
            ;;
        esac
    ;;
    linux*) PLATFORM=linux ;;
    msys*) PLATFORM=win32 ;;
    *)
        echo "Unrecognized OS: $OSTYPE"
        exit 1
    ;;
esac

cd "$(dirname "$0")/.."
rm -rf vendored
mkdir vendored
cd vendored

curl -Lo ffmpeg-miniredis.zip "https://tomato.nyc3.digitaloceanspaces.com/ffmpeg-miniredis-$PLATFORM.zip"
unzip ffmpeg-miniredis.zip
rm ffmpeg-miniredis.zip

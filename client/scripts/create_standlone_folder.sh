#!/bin/bash

set -e

cd "$(dirname "$0")/.."

POETRY_VERSION=1.3.2

PYTHON_RELEASE=20230116
PYTHON_VERSION=3.11.1
PYTHON_MAJOR_VERSION="$(echo "$PYTHON_VERSION" | cut -d '.' -f 1-2)"
PYTHON_URL_PREFIX="https://github.com/indygreg/python-build-standalone/releases/download/${PYTHON_RELEASE}"

FFMPEG_RELEASE=b5.0.1
FFMPEG_URL_PREFIX="https://github.com/eugeneware/ffmpeg-static/releases/download/${FFMPEG_RELEASE}"

FFPROBE_RELEASE=73b68af8
FFPROBE_URL_PREFIX="https://github.com/joshwnj/ffprobe-static/raw/${FFPROBE_RELEASE}/bin"

STANDALONE_DIR="$(pwd)/standalone"

case "$OSTYPE" in
    msys)
        PLATFORM=Windows
        PYTHON_TARGET=pc-windows-msvc-shared
        FFMPEG_TARGET=win32
        ;;

    linux*)
        PLATFORM=Linux
        PYTHON_TARGET=unknown-linux-gnu
        FFMPEG_TARGET=linux
        ;;
    darwin*)
        PLATFORM=macOS
        PYTHON_TARGET=apple-darwin
        FFMPEG_TARGET=darwin
        ;;
    *)
        echo "Unknown operating system: $OSTYPE"
        exit 1
        ;;
esac

echo "Building for $PLATFORM"

if [ -e "$STANDALONE_DIR" ]; then
    echo 'Removing existing standalone directory'
    rm -rf "$STANDALONE_DIR"
fi

mkdir -p "$STANDALONE_DIR"

PYTHON_TARBALL="cpython-${PYTHON_VERSION}+${PYTHON_RELEASE}-x86_64-${PYTHON_TARGET}-install_only.tar.gz"
PYTHON_URL="${PYTHON_URL_PREFIX}/${PYTHON_TARBALL}"

echo "Downloading $PYTHON_TARBALL"
curl -fsSL "$PYTHON_URL" | tar xz -C "$STANDALONE_DIR" --strip-components=1

"$STANDALONE_DIR/bin/pip" install --no-cache-dir "poetry==${POETRY_VERSION}" pip-autoremove

cd ../server
export POETRY_VIRTUALENVS_CREATE=false
"$STANDALONE_DIR/bin/poetry" install --without=server --without=dev
cd ../client

echo 'Removing unnecessary python files'
"$STANDALONE_DIR/bin/pip-autoremove" --yes poetry
"$STANDALONE_DIR/bin/pip" uninstall --yes pip-autoremove
find "$STANDALONE_DIR" | grep -E '(/__pycache__$|\.pyc$|\.pyo$)' | xargs rm -rf

cd standalone/bin
echo 'Downloading ffmpeg'

if [ "$FFMPEG_TARGET" = darwin ]; then
    # Universal binary for ffmpeg, beacuse why not
    curl -fsSL "${FFMPEG_URL_PREFIX}/darwin-x64.gz" | gzip -d > ffmpeg-x64
    curl -fsSL "${FFMPEG_URL_PREFIX}/darwin-arm64.gz" | gzip -d > ffmpeg-arm64
    chmod +x ffmpeg-x64 ffmpeg-arm64
    lipo ffmpeg-x64 ffmpeg-arm64 -create -output ffmpeg
    rm ffmpeg-x64 ffmpeg-arm64
else
    curl -fsSL "${FFMPEG_URL_PREFIX}/${FFMPEG_TARGET}-x64.gz" | gzip -d > ffmpeg
    chmod +x ffmpeg
fi

echo 'Downloading ffprobe'
curl -fsSL -o ffprobe "${FFPROBE_URL_PREFIX}/${FFMPEG_TARGET}/x64/ffprobe"
chmod +x ffprobe

echo 'Done!'

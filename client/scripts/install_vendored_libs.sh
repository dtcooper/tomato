#!/bin/bash

cd "$(dirname "$0")/.."

if [ "$1" != "--force" -a -d vendor ]; then
    echo "Vendored libs already installed. Use --force to reinstall"
    exit 0
fi

set -ex

ARCH=x64
PYTHON_ARCH=x86_64
case "$OSTYPE" in
    darwin*)
        PLATFORM=darwin
        PYTHON_DIST=apple-darwin
        if [ "$(uname -m)" = arm64 ]; then
            ARCH=arm64
        fi
    ;;
    linux*)
        PLATFORM=linux
        PYTHON_ARCH=x86_64_v2
        PYTHON_DIST=unknown-linux-gnu
    ;;
    msys*)
        PLATFORM=win32
        PYTHON_DIST=pc-windows-msvc-shared
    ;;
    *)
        echo "Unrecognized OS: $OSTYPE"
        exit 1
    ;;
esac

POETRY_VERSION='1.5.1'
PYTHON_RELEASE_DATE=20230507
PYTHON_VERSION='3.11.3'
PYTHON_STANDLONE_REPO='indygreg/python-build-standalone'
PYTHON_URL_PREFIX="https://github.com/${PYTHON_STANDLONE_REPO}/releases/download/${PYTHON_RELEASE_DATE}"
FFMPEG_MINIREDIS_URL="https://tomato.nyc3.digitaloceanspaces.com/ffmpeg-miniredis-${PLATFORM}.zip"

echo "Installing vendored libraries for $PLATFORM"

get_python_url () {
    __PYTHON_ARCH="$PYTHON_ARCH"
    if [ "$1" ]; then
        __PYTHON_ARCH="$1"
    fi
    echo "${PYTHON_URL_PREFIX}/cpython-${PYTHON_VERSION}+${PYTHON_RELEASE_DATE}-${__PYTHON_ARCH}-${PYTHON_DIST}-install_only.tar.gz"
}

rm -rf vendor
mkdir vendor
cd vendor

mkdir python-x64
curl -L "$(get_python_url)" | tar xz -C python-x64 --strip-components=1

if [ "$PLATFORM" = darwin ]; then
    mkdir python-arm64
    curl -L "$(get_python_url aarch64)" | tar xz -C python-arm64 --strip-components=1
fi

PYTHON_BIN="python-${ARCH}/bin/python3"
if [ "$PLATFORM" = win32 ]; then
    PYTHON_BIN="python-${ARCH}/python.exe"
fi
PYTHON_BIN="${PWD}/${PYTHON_BIN}"

TEMP_DIR="$(mktemp -d)"
POETRY_DIR="${TEMP_DIR}/poetry"
REQUIREMENTS="${TEMP_DIR}/requirements.txt"
export PYTHONDONTWRITEBYTECODE=1

"$PYTHON_BIN" -B -m pip install --isolated --no-compile --target "$POETRY_DIR" "poetry==${POETRY_VERSION}"

cd ../../server
PYTHONPATH="$POETRY_DIR" "$PYTHON_BIN" -B -m poetry export --with=standalone --without-hashes -o "$REQUIREMENTS"
cd ../client/vendor
"$PYTHON_BIN" -B -m pip install --isolated --no-compile --target pypackages -r "$REQUIREMENTS"
rm -rf pypackages/bin

curl -Lo "${TEMP_DIR}/ffmpeg-miniredis.zip" "https://tomato.nyc3.digitaloceanspaces.com/ffmpeg-miniredis-$PLATFORM.zip"
unzip "${TEMP_DIR}/ffmpeg-miniredis.zip"

rm -rf "$TEMP_DIR"

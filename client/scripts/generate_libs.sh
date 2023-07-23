#!/bin/sh

# Should only be run on Linux, but generates for all three platforms

set -e

POETRY_VERSION='1.5.1'
RUST_VERSION='1.71.0'
RUST_DARWIN_BUILDER="joseluisq/rust-linux-darwin-builder:${RUST_VERSION}"
RUST_BUILDER="rust:${RUST_VERSION}"
MINI_REDIS_VERSION='573283f36723cb0321cd3bbac16fae798d093baf'
MINI_REDIS_URL="https://github.com/tokio-rs/mini-redis/tarball/${MINI_REDIS_VERSION}"

LINUX_PYTHON_URL='https://github.com/indygreg/python-build-standalone/releases/download/20230507/cpython-3.11.3+20230507-x86_64-unknown-linux-gnu-install_only.tar.gz'
LINUX_FFMPEG_URL='https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz'
WIN32_FFMPEG_URL='https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z'
MACOS_ARM_FFMPEG_URL='https://www.osxexperts.net/ffmpeg6arm.zip'
MACOS_X64_FFMPEG_URL='https://www.osxexperts.net/ffmpeg6intel.zip'
MACOS_ARM_FFPROBE_URL='https://www.osxexperts.net/ffprobe6arm.zip'
MACOS_X64_FFPROBE_URL='https://www.osxexperts.net/ffprobe6intel.zip'


cd "$(dirname "$0")/.."
rm -rf libs
mkdir libs
cd libs

LIBS_DIR="$(realpath .)"
SERVER_DIR="$(realpath ../../server)"
TEMP_DIR="$(mktemp -d)"

mkdir linux darwin win32

##### Python
echo 'python/linux'
export PYTHONDONTWRITEBYTECODE=1
export POETRY_VIRTUALENVS_CREATE=false

cd linux
curl -L "$LINUX_PYTHON_URL" | tar xz
mv python python-x64

# Install poetry to get requirements file
./python-x64/bin/pip install "poetry==$POETRY_VERSION" pip-autoremove
cd "$SERVER_DIR"
"${LIBS_DIR}/linux/python-x64/bin/poetry" env remove --all  # Won't work if there's an existing poetry environment
"${LIBS_DIR}/linux/python-x64/bin/poetry" install --without=server --without=dev
cd "${LIBS_DIR}/linux"

./python-x64/bin/pip-autoremove -y poetry
./python-x64/bin/pip uninstall -y pip-autoremove

# ##### mini-redis
# echo 'mini-redis'


# #Linux and Windows
# echo 'mini-redis-server/linux + mini-redis-server/win32'
# docker run --rm -i -v "$(realpath .):/mnt" -w /root "$RUST_BUILDER" <<EOF
# apt-get update
# apt-get upgrade -y
# apt-get install -y --no-install-recommends gcc-mingw-w64-x86-64-win32
# rustup target add x86_64-pc-windows-gnu x86_64-unknown-linux-gnu
# mkdir mini-redis
# curl -L '$MINI_REDIS_URL' | tar xz -C mini-redis --strip-components=1
# cd mini-redis
# cargo build --release --target x86_64-pc-windows-gnu --target x86_64-unknown-linux-gnu --bin mini-redis-server
# cp -v target/x86_64-pc-windows-gnu/release/mini-redis-server.exe /mnt/win32
# cp -v target/x86_64-unknown-linux-gnu/release/mini-redis-server /mnt/linux
# EOF

# # macOS
# echo 'mini-redis-server/darwin'
# docker run --rm -i -v "$(realpath .)/darwin:/mnt" "$RUST_DARWIN_BUILDER" <<EOF
# rustup target add aarch64-apple-darwin x86_64-apple-darwin
# mkdir mini-redis
# curl -L '$MINI_REDIS_URL' | tar xz -C mini-redis --strip-components=1
# cd mini-redis
# cargo build --release --target aarch64-apple-darwin --target x86_64-apple-darwin --bin mini-redis-server
# lipo target/aarch64-apple-darwin/release/mini-redis-server \
#     target/x86_64-apple-darwin/release/mini-redis-server -create -output /mnt/mini-redis-server
# EOF


# ##### ffmpeg
# echo 'ffmpeg'

# # Linux
# echo 'ffmpeg/linux'
# mkdir "${TEMP_DIR}/ffmpeg-linux"
# curl -L "$LINUX_FFMPEG_URL" | tar xJ -C "${TEMP_DIR}/ffmpeg-linux"
# mv -v "${TEMP_DIR}/ffmpeg-linux/ffmpeg-6.0-amd64-static/ffmpeg" \
#     "${TEMP_DIR}/ffmpeg-linux/ffmpeg-6.0-amd64-static/ffprobe" linux

# # Windows
# echo 'ffmpeg/win32'
# mkdir "${TEMP_DIR}/ffmpeg-win32"
# cd "${TEMP_DIR}/ffmpeg-win32"
# curl -Lo ffmpeg.7z "$WIN32_FFMPEG_URL"
# 7z x ffmpeg.7z
# cd "$LIBS_DIR"
# mv -v "${TEMP_DIR}/ffmpeg-win32/ffmpeg-6.0-full_build/bin/ffmpeg.exe" \
#     "${TEMP_DIR}/ffmpeg-win32/ffmpeg-6.0-full_build/bin/ffprobe.exe" win32

# # macOS
# echo 'ffmpeg/darwin'
# mkdir "${TEMP_DIR}/ffmpeg-darwin"
# cd "${TEMP_DIR}/ffmpeg-darwin"
# curl -Lo ffmpeg-arm.zip "$MACOS_ARM_FFMPEG_URL"
# unzip -o ffmpeg-arm.zip
# mv -v ffmpeg ffmpeg-arm
# curl -Lo ffmpeg-x64.zip "$MACOS_X64_FFMPEG_URL"
# unzip -o ffmpeg-x64.zip
# mv -v ffmpeg ffmpeg-x64
# curl -Lo ffprobe-arm.zip "$MACOS_ARM_FFPROBE_URL"
# unzip -o ffprobe-arm.zip
# mv -v ffprobe ffprobe-arm
# curl -Lo ffprobe-x64.zip "$MACOS_X64_FFPROBE_URL"
# unzip -o ffprobe-x64.zip
# mv -v ffprobe ffprobe-x64

# # Create universal binaries
# docker run --rm -i -v "$(realpath .):/mnt" -w /mnt "$RUST_DARWIN_BUILDER" <<'EOF'
# lipo ffmpeg-arm ffmpeg-x64 -create -output ffmpeg
# lipo ffprobe-arm ffprobe-x64 -create -output ffprobe
# EOF

# cd "$LIBS_DIR"
# mv -v "${TEMP_DIR}/ffmpeg-darwin/ffmpeg" "${TEMP_DIR}/ffmpeg-darwin/ffprobe" darwin

rm -rf "$TEMP_DIR"

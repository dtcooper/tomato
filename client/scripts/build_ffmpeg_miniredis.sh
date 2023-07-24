#!/bin/sh

# Should only be run on Linux, but generates for all three platforms

set -ex

RUST_VERSION='1.71.0'
RUST_DARWIN_BUILDER="joseluisq/rust-linux-darwin-builder:${RUST_VERSION}"
RUST_BUILDER="rust:${RUST_VERSION}"
MINI_REDIS_VERSION='573283f36723cb0321cd3bbac16fae798d093baf'
MINI_REDIS_URL="https://github.com/tokio-rs/mini-redis/tarball/${MINI_REDIS_VERSION}"

LINUX_FFMPEG_URL='https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz'
WIN32_FFMPEG_URL='https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z'
MACOS_ARM_FFMPEG_URL='https://www.osxexperts.net/ffmpeg6arm.zip'
MACOS_X64_FFMPEG_URL='https://www.osxexperts.net/ffmpeg6intel.zip'
MACOS_ARM_FFPROBE_URL='https://www.osxexperts.net/ffprobe6arm.zip'
MACOS_X64_FFPROBE_URL='https://www.osxexperts.net/ffprobe6intel.zip'

cd "$(dirname "$0")"

LIBS_DIR="$(realpath .)/libs"
rm -rf "${LIBS_DIR}"
TEMP_DIR="$(mktemp -d)"

mkdir "${TEMP_DIR}/linux" "${TEMP_DIR}/darwin" "${TEMP_DIR}/win32"
echo "Building in ${TEMP_DIR}"
cd "${TEMP_DIR}"

# mini-redis

# Linux and Windows
echo 'GENERATING: mini-redis-server/linux + mini-redis-server/win32'
docker run --rm -i -v "${TEMP_DIR}:/mnt" -w /root "$RUST_BUILDER" <<EOF
apt-get update
apt-get upgrade -y
apt-get install -y --no-install-recommends gcc-mingw-w64-x86-64-win32
rustup target add x86_64-pc-windows-gnu x86_64-unknown-linux-gnu
mkdir mini-redis
curl -L '$MINI_REDIS_URL' | tar xz -C mini-redis --strip-components=1
cd mini-redis
cargo build --release --target x86_64-pc-windows-gnu --target x86_64-unknown-linux-gnu --bin mini-redis-server
cp -v target/x86_64-pc-windows-gnu/release/mini-redis-server.exe /mnt/win32
cp -v target/x86_64-unknown-linux-gnu/release/mini-redis-server /mnt/linux
EOF

# macOS
echo 'GENERATING: mini-redis-server/darwin'
docker run --rm -i -v "${TEMP_DIR}/darwin:/mnt" "$RUST_DARWIN_BUILDER" <<EOF
rustup target add aarch64-apple-darwin x86_64-apple-darwin
mkdir mini-redis
curl -L '$MINI_REDIS_URL' | tar xz -C mini-redis --strip-components=1
cd mini-redis
cargo build --release --target aarch64-apple-darwin --target x86_64-apple-darwin --bin mini-redis-server
lipo target/aarch64-apple-darwin/release/mini-redis-server \
    target/x86_64-apple-darwin/release/mini-redis-server -create -output /mnt/mini-redis-server
EOF

# ffmpeg

# Linux
echo 'GENERATING: ffmpeg/linux'

mkdir -p ffmpeg-build/linux
curl -L "$LINUX_FFMPEG_URL" | tar xJ -C ffmpeg-build/linux
mv -v ffmpeg-build/linux/ffmpeg-6.0-amd64-static/ffmpeg \
    ffmpeg-build/linux/ffmpeg-6.0-amd64-static/ffprobe linux

# Windows
echo 'GENERATING: ffmpeg/win32'
mkdir ffmpeg-build/win32
cd ffmpeg-build/win32
curl -Lo ffmpeg.7z "$WIN32_FFMPEG_URL"
7z x ffmpeg.7z
cd ../..
mv -v ffmpeg-build/win32/ffmpeg-6.0-full_build/bin/ffmpeg.exe \
    ffmpeg-build/win32/ffmpeg-6.0-full_build/bin/ffprobe.exe win32

# macOS
echo 'GENERATING: ffmpeg/darwin'
mkdir ffmpeg-build/darwin
cd ffmpeg-build/darwin
curl -Lo ffmpeg-arm.zip "$MACOS_ARM_FFMPEG_URL"
unzip -o ffmpeg-arm.zip
mv -v ffmpeg ffmpeg-arm
curl -Lo ffmpeg-x64.zip "$MACOS_X64_FFMPEG_URL"
unzip -o ffmpeg-x64.zip
mv -v ffmpeg ffmpeg-x64
curl -Lo ffprobe-arm.zip "$MACOS_ARM_FFPROBE_URL"
unzip -o ffprobe-arm.zip
mv -v ffprobe ffprobe-arm
curl -Lo ffprobe-x64.zip "$MACOS_X64_FFPROBE_URL"
unzip -o ffprobe-x64.zip
mv -v ffprobe ffprobe-x64
cd ../..

# Create universal binaries
docker run --rm -i -v "${TEMP_DIR}:/mnt" -w /mnt/ffmpeg-build/darwin "$RUST_DARWIN_BUILDER" <<'EOF'
lipo ffmpeg-arm ffmpeg-x64 -create -output ../../darwin/ffmpeg
lipo ffprobe-arm ffprobe-x64 -create -output ../../darwin/ffprobe
EOF

echo "GENERATING: zip archives at ${LIBS_DIR}"
mkdir "$LIBS_DIR"
cd linux
zip -9 "${LIBS_DIR}/ffmpeg-miniredis-linux.zip" *
cd ../darwin
zip -9 "${LIBS_DIR}/ffmpeg-miniredis-darwin.zip" *
cd ../win32
zip -9 "${LIBS_DIR}/ffmpeg-miniredis-win32.zip" *

cd "$LIBS_DIR"
rm -rf "$TEMP_DIR"
echo 'Done.'

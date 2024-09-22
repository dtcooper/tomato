FROM --platform="${BUILDPLATFORM}" messense/rust-musl-cross:x86_64-musl AS minijina-builder-amd64
FROM --platform="${BUILDPLATFORM}" messense/rust-musl-cross:aarch64-musl AS minijina-builder-arm64
FROM --platform="${BUILDPLATFORM}" "minijina-builder-${TARGETARCH}" AS minijina-builder

ARG BUILDARCH
ARG TARGETARCH

ARG MINIJINJA_VERSION=2.3.1
RUN echo "Building for arch ${TARGETARCH} on ${BUILDARCH}" \
    && BUILD_TARGET="$([ "${TARGETARCH}" = amd64 ] && echo x86_64 || echo aarch64)-unknown-linux-musl" \
    && cargo install \
            --target "${BUILD_TARGET}" \
            --root /build \
            --version "${MINIJINJA_VERSION}" \
            --no-default-features \
        minijinja-cli \
    && "/usr/local/musl/${BUILD_TARGET}/bin/strip" /build/bin/minijinja-cli


FROM jonasal/nginx-certbot:5.4-alpine AS final

COPY --from=minijina-builder /build/bin/minijinja-cli /usr/local/bin/
COPY image/ /

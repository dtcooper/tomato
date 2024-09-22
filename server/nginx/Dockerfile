# Cross-compile minijinja-cli
FROM --platform="${BUILDPLATFORM}" messense/rust-musl-cross:x86_64-musl AS minijinja-amd64
FROM --platform="${BUILDPLATFORM}" messense/rust-musl-cross:aarch64-musl AS minijinja-arm64
FROM "minijinja-${TARGETARCH}" AS minijinja

ARG BUILDARCH

ARG MINIJINJA_VERSION=2.3.1
RUN echo "Building for ${RUST_MUSL_CROSS_TARGET} on ${BUILDARCH}" \
    && cargo install \
            --no-default-features \
            --root /build \
            --target "${RUST_MUSL_CROSS_TARGET}" \
            --version "${MINIJINJA_VERSION}" \
        minijinja-cli \
    && "${TARGET_HOME}/bin/strip" /build/bin/minijinja-cli


FROM jonasal/nginx-certbot:5.4-alpine AS final

COPY --from=minijinja /build/bin/minijinja-cli /usr/local/bin/
COPY image/ /

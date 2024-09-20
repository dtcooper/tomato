FROM rust:alpine AS minijina-builder

ARG MINIJINJA_VERSION=2.3.1
RUN cargo install \
            --root /build \
            --version "${MINIJINJA_VERSION}" \
            --no-default-features \
        minijinja-cli \
    && strip /build/bin/minijinja-cli


FROM jonasal/nginx-certbot:5.4-alpine AS final

COPY --from=minijina-builder /build/bin/minijinja-cli /usr/local/bin/
COPY image/ /

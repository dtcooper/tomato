ARG CONTAINER="jonasal/nginx-certbot:5.4-alpine"


FROM "${CONTAINER}" AS minijinja-builder

RUN apk add --no-cache cargo

ARG MINIJINJA_VERSION=2.3.1
RUN cargo install \
            --root /build \
            --version "${MINIJINJA_VERSION}" \
            --no-default-features \
        minijinja-cli \
    && strip /build/bin/minijinja-cli


FROM "${CONTAINER}" AS final

COPY --from=minijinja-builder /build/bin/minijinja-cli /usr/local/bin/
COPY image/ /

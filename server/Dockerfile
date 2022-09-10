FROM python:3.10-bullseye AS base


FROM base AS audiowaveform-builder

ARG AUDIOWAVEFORM_VERSION=1.6.0

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y \
        cmake \
        g++ \
        gcc \
        libboost-filesystem-dev \
        libboost-program-options-dev \
        libboost-regex-dev \
        libgd-dev \
        libid3tag0-dev \
        libmad0-dev \
        libsndfile1-dev \
        make \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/src/audiowaveform && cd /usr/src/audiowaveform \
    && wget -qO - "https://github.com/bbc/audiowaveform/archive/refs/tags/${AUDIOWAVEFORM_VERSION}.tar.gz" | tar xz --strip-components 1 \
    && mkdir build && cd build \
    && cmake -D ENABLE_TESTS=0 .. \
    && make && make install && strip "$(which audiowaveform)"


FROM base AS final

ARG DEBUG=0 \
    POETRY_VERSION=1.2.0 \
    WAIT_FOR_IT_VERSION=81b1373f

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN wget -qO /usr/local/bin/wait-for-it \
        "https://raw.githubusercontent.com/vishnubob/wait-for-it/${WAIT_FOR_IT_VERSION}/wait-for-it.sh" \
    && chmod +x /usr/local/bin/wait-for-it

RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH="/root/.local/bin:${PATH}"

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y \
        ffmpeg \
        # For audiowaveform
        libboost-filesystem1.74.0 \
        libboost-program-options1.74.0 \
        libboost-regex1.74.0 \
        libgd3 \
        libid3tag0 \
        libmad0 \
        libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock /app/
WORKDIR /app
RUN poetry install $([ -z "$DEBUG" -o "$DEBUG" = '0' ] && echo '--no-dev')

COPY --from=audiowaveform-builder /usr/local/bin/audiowaveform /usr/local/bin/
COPY *.py *.sh tomato /app/
WORKDIR /app

ENTRYPOINT ["/app/entrypoint.sh"]
CMD []

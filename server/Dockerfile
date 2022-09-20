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

RUN mkdir -p /usr/src/audiowaveform \
    && cd /usr/src/audiowaveform \
    && wget -qO - "https://github.com/bbc/audiowaveform/archive/refs/tags/${AUDIOWAVEFORM_VERSION}.tar.gz" | tar xz --strip-components 1 \
    && mkdir build && cd build \
    && cmake -D ENABLE_TESTS=0 .. \
    && make -j "$(nproc)" \
    && make install \
    && strip "$(which audiowaveform)"


FROM base AS final

ARG DEBUG=0 \
    DJANGO_BASH_COMPLETION_VERSION=4.1 \
    POETRY_VERSION=1.2.1 \
    WAIT_FOR_IT_VERSION=81b1373f

ENV DJANGO_SETTINGS_MODULE=tomato.settings \
    PYTHONDONTWRITEBYTECODE=1 \
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
        $([ "$DEBUG" -a "$DEBUG" != '0' ] && echo \
            bash-completion \
            less \
            iputils-ping \
            nano \
            netcat \
            postgresql-client \
            redis-tools \
        ) \
    && rm -rf /var/lib/apt/lists/* \
    && if [ "$DEBUG" -a "$DEBUG" != '0' ]; then \
        echo "alias redis-cli='redis-cli -h redis'" >> /root/.bashrc \
        && echo "alias ls='ls --color=auto'" >> /root/.bashrc \
        && echo '. /etc/bash_completion' >> /root/.bashrc \
        && wget -qO /etc/bash_completion.d/django_bash_completion \
            "https://raw.githubusercontent.com/django/django/${DJANGO_BASH_COMPLETION_VERSION}/extras/django_bash_completion" \
    ; fi

COPY pyproject.toml poetry.lock /app/
WORKDIR /app
RUN poetry install $([ -z "$DEBUG" -o "$DEBUG" = '0' ] && echo '--without=dev')

COPY --from=audiowaveform-builder /usr/local/bin/audiowaveform /usr/local/bin/
COPY --from=quay.io/minio/mc:RELEASE.2022-09-16T09-16-47Z /usr/bin/mc /usr/local/bin/
COPY *.py *.sh /app/
COPY tomato/ /app/tomato/
WORKDIR /app

ENTRYPOINT ["/app/entrypoint.sh"]
CMD []

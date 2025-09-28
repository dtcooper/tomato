ARG DEBIAN_VERSION=bookworm
ARG NODE_VERSION=22
ARG PYTHON_VERSION=3.13


# Install and build node-related files for front-end
FROM "node:${NODE_VERSION}-${DEBIAN_VERSION}-slim" AS node-packages

COPY /tomato/static/vendor /vendor/
WORKDIR /vendor

RUN npm install


FROM "python:${PYTHON_VERSION}-${DEBIAN_VERSION}" AS final

ENV DJANGO_SETTINGS_MODULE=tomato.settings \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

ARG DEBUG=0
RUN if [ "$DEBUG" -a "$DEBUG" != '0' ]; then \
        curl -fsSL "https://deb.nodesource.com/setup_${NODE_VERSION}.x" | sh \
    ; fi \
    && apt-get update \
    && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y \
        ffmpeg \
        sox \
        $([ "$DEBUG" -a "$DEBUG" != '0' ] && echo \
            bash-completion \
            iputils-ping \
            less \
            nano \
            netcat-openbsd \
            npm \
            postgresql-client \
            sqlite3 \
            watchman \
        ) \
    && rm -rf /var/lib/apt/lists/* \
    && if [ "$DEBUG" -a "$DEBUG" != '0' ]; then \
        echo "alias ls='ls --color=auto'" >> /root/.bashrc \
        && echo "alias rs='__SKIP_CHECKS=1 /app/entrypoint.sh'" >> /root/.bashrc \
        && echo "alias rs_debug='___SKIP_CHECKS=1 TOMATO_DEBUG_LOG=1 /app/entrypoint.sh'" >> /root/.bashrc \
        && echo "alias sp='./manage.py shell_plus'" >> /root/.bashrc \
        && echo "alias lint='black . ; isort . ; flake8 .'" >> /root/.bashrc \
        && echo '. /etc/bash_completion' >> /root/.bashrc \
    ; fi

ARG POETRY_VERSION=2.2.1
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH="/root/.local/bin:${PATH}"
RUN echo '/app' > "$(python -c 'import site; print(site.getsitepackages()[0])')/app.pth"

COPY pyproject.toml poetry.lock /app/
WORKDIR /app
RUN poetry install $([ -z "$DEBUG" -o "$DEBUG" = '0' ] && echo '--without=dev') \
    && if [ "$DEBUG" -a "$DEBUG" != 0 ]; then \
        # Download relevant verion's bash completion (in dev only)
        wget -qO /etc/bash_completion.d/django_bash_completion \
            "https://raw.githubusercontent.com/django/django/$(python -c 'import django; print(".".join(map(str, django.VERSION[:2])))')/extras/django_bash_completion" \
    ; fi

COPY *.py *.sh constants.json /app/
COPY tomato/ /app/tomato/
COPY api/ /app/api/
COPY --from=node-packages /vendor/node_modules/ /app/tomato/static/vendor/node_modules/
WORKDIR /app

ENTRYPOINT ["/app/entrypoint.sh"]
CMD []

# Add frozen version to container
ARG TOMATO_VERSION
RUN if [ "$TOMATO_VERSION" ]; then \
        echo "$TOMATO_VERSION" > .tomato_version \
    ; fi

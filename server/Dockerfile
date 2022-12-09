FROM python:3.11-bullseye


ENV DJANGO_SETTINGS_MODULE=tomato.settings \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

ARG WAIT_FOR_IT_VERSION=81b1373f
RUN wget -qO /usr/local/bin/wait-for-it \
        "https://raw.githubusercontent.com/vishnubob/wait-for-it/${WAIT_FOR_IT_VERSION}/wait-for-it.sh" \
    && chmod +x /usr/local/bin/wait-for-it

ARG POETRY_VERSION=1.3.0
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH="/root/.local/bin:${PATH}"

ARG DEBUG=0 \
    DJANGO_BASH_COMPLETION_VERSION=4.1
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y \
        ffmpeg \
        sox \
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

COPY constants.json pyproject.toml poetry.lock /app/
WORKDIR /app
RUN poetry install $([ -z "$DEBUG" -o "$DEBUG" = '0' ] && echo '--without=dev')

COPY *.py *.sh /app/
COPY tomato/ /app/tomato/
WORKDIR /app

ENTRYPOINT ["/app/entrypoint.sh"]
CMD []

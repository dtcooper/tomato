ARG DEBIAN_VERSION=bookworm
ARG NODE_VERSION=22


# Install and build node-related files for front-end
FROM "node:${NODE_VERSION}-${DEBIAN_VERSION}-slim" AS node-packages

COPY /tomato/static/vendor /vendor/
WORKDIR /vendor

RUN npm install


# Taken from Python 3.13 dockerfile, add experimental JIT
FROM buildpack-deps:bookworm AS jit

# ensure local python is preferred over distribution python
ENV PATH /usr/local/bin:$PATH

# runtime dependencies
RUN set -eux; \
	apt-get update; \
	apt-get install -y --no-install-recommends \
		libbluetooth-dev \
		lsb-release \
		software-properties-common \
		tk-dev \
		uuid-dev \
	; \
	rm -rf /var/lib/apt/lists/*

ENV GPG_KEY 7169605F62C751356D054A26A821E680E5FA6305
ENV PYTHON_VERSION 3.13.0

RUN set -eux; \
	\
	wget https://apt.llvm.org/llvm.sh; \
	chmod +x llvm.sh; \
	./llvm.sh 18; \
	rm llvm.sh; \
	wget -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz"; \
	wget -O python.tar.xz.asc "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz.asc"; \
	GNUPGHOME="$(mktemp -d)"; export GNUPGHOME; \
	gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys "$GPG_KEY"; \
	gpg --batch --verify python.tar.xz.asc python.tar.xz; \
	gpgconf --kill all; \
	rm -rf "$GNUPGHOME" python.tar.xz.asc; \
	mkdir -p /usr/src/python; \
	tar --extract --directory /usr/src/python --strip-components=1 --file python.tar.xz; \
	rm python.tar.xz; \
	\
	cd /usr/src/python; \
	gnuArch="$(dpkg-architecture --query DEB_BUILD_GNU_TYPE)"; \
	./configure \
		--build="$gnuArch" \
		--enable-experimental-jit=yes-off \
		--enable-loadable-sqlite-extensions \
		--enable-optimizations \
		--enable-option-checking=fatal \
		--enable-shared \
		--with-lto \
		--with-system-expat \
		--with-ensurepip \
	; \
	nproc="$(nproc)"; \
	EXTRA_CFLAGS="$(dpkg-buildflags --get CFLAGS)"; \
	LDFLAGS="$(dpkg-buildflags --get LDFLAGS)"; \
	make -j "$nproc" \
		"EXTRA_CFLAGS=${EXTRA_CFLAGS:-}" \
		"LDFLAGS=${LDFLAGS:-}" \
		"PROFILE_TASK=${PROFILE_TASK:-}" \
	; \
# https://github.com/docker-library/python/issues/784
# prevent accidental usage of a system installed libpython of the same version
	rm python; \
	make -j "$nproc" \
		"EXTRA_CFLAGS=${EXTRA_CFLAGS:-}" \
		"LDFLAGS=${LDFLAGS:--Wl},-rpath='\$\$ORIGIN/../lib'" \
		"PROFILE_TASK=${PROFILE_TASK:-}" \
		python \
	; \
	make install; \
	\
# enable GDB to load debugging data: https://github.com/docker-library/python/pull/701
	bin="$(readlink -ve /usr/local/bin/python3)"; \
	dir="$(dirname "$bin")"; \
	mkdir -p "/usr/share/gdb/auto-load/$dir"; \
	cp -vL Tools/gdb/libpython.py "/usr/share/gdb/auto-load/$bin-gdb.py"; \
	\
	cd /; \
	rm -rf /usr/src/python; \
	\
	find /usr/local -depth \
		\( \
			\( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
			-o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \) \) \
		\) -exec rm -rf '{}' + \
	; \
	\
	ldconfig; \
	\
	export PYTHONDONTWRITEBYTECODE=1; \
	python3 --version; \
	pip3 --version

# make some useful symlinks that are expected to exist ("/usr/local/bin/python" and friends)
RUN set -eux; \
	for src in idle3 pip3 pydoc3 python3 python3-config; do \
		dst="$(echo "$src" | tr -d 3)"; \
		[ -s "/usr/local/bin/$src" ]; \
		[ ! -e "/usr/local/bin/$dst" ]; \
		ln -svT "$src" "/usr/local/bin/$dst"; \
	done

CMD ["python3"]


# FROM "python:${PYTHON_VERSION}-${DEBIAN_VERSION}" AS final
FROM jit AS final

ENV DJANGO_SETTINGS_MODULE=tomato.settings \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHON_JIT=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

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
            nodejs \
            npm \
            postgresql-client \
            sqlite3 \
            watchman \
        ) \
    && rm -rf /var/lib/apt/lists/* \
    && if [ "$DEBUG" -a "$DEBUG" != '0' ]; then \
        echo "alias ls='ls --color=auto'" >> /root/.bashrc \
        && echo "alias rs='__SKIP_CHECKS=1 /app/entrypoint.sh'" >> /root/.bashrc \
        && echo "alias sp='./manage.py shell_plus'" >> /root/.bashrc \
        && echo '. /etc/bash_completion' >> /root/.bashrc \
    ; fi

ARG POETRY_VERSION=1.8.3
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH="/root/.local/bin:${PATH}"
# Add tomato to Python path permanently
RUN echo '/app' > "$(python -c 'import site; print(site.getsitepackages()[0])')/tomato.pth"

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

ARG DOCKER_NGINX_CERTBOT_VERSION=5.4


FROM "jonasal/nginx-certbot:${DOCKER_NGINX_CERTBOT_VERSION}-alpine" AS final

ARG PIP_BREAK_SYSTEM_PACKAGES=1
ARG JINJANATOR_VERSION=24.3.0

RUN pip install --no-cache-dir "jinjanator==${JINJANATOR_VERSION}"

ADD image/ /

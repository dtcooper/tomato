FROM jonasal/nginx-certbot:5.3-alpine

ARG PIP_BREAK_SYSTEM_PACKAGES=1
ARG JINJANATOR_VERSION=24.3.0

RUN pip install --no-cache-dir "jinjanator==${JINJANATOR_VERSION}"

ADD image/ /

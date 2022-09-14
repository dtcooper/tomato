COMPOSE:=docker compose
CONTAINERS:=
CONTAINER:=app

.PHONY: build
build:
	$(COMPOSE) build --pull $(CONTAINERS)

.PHONY: shell
shell:
	$(COMPOSE) run --rm --service-ports --use-aliases $(CONTAINER) bash

.PHONY: up
up:
	$(COMPOSE) up

.PHONY: down
down:
	$(COMPOSE) down

.PHONY: check-env
check-env:
	@for f in .env .env.sample ; do \
		sed 's/^\([A-Z_]*\)=.*/\1/' "$$f" > "/tmp/diff-$$f" ; \
	done ; \
	colordiff -u /tmp/diff-.env.sample /tmp/diff-.env ; \
	rm /tmp/diff-.env*

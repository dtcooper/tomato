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

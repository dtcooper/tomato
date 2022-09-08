COMPOSE:=docker compose

CONTAINERS:=
.PHONY: build
build:
	$(COMPOSE) build --pull $(CONTAINERS)

.PHONY: shell
CONTAINER:=app
shell:
	$(COMPOSE) run --rm --service-ports --use-aliases $(CONTAINER) bash

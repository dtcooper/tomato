COMPOSE:=docker compose
CONTAINERS:=
CONTAINER:=app

.PHONY: build
build:
	$(COMPOSE) build --pull $(CONTAINERS)

.PHONY: shell
shell:
	$(COMPOSE) run --rm --service-ports --use-aliases $(CONTAINER) bash || true

.PHONY: up
up:
	$(COMPOSE) up --remove-orphans $(shell source .env; if [ -z "$$DEBUG" -o "$$DEBUG" = 0 ]; then echo "-d"; fi) || true

.PHONY: down
down:
	$(COMPOSE) down --remove-orphans

.PHONY: check-env
check-env:
	@for f in .env .env.sample ; do \
		sed 's/^#//' "$$f" | sed 's/^\([A-Z_]*\)=.*/\1/' > "/tmp/diff-$$f" ; \
	done ; \
	colordiff -u /tmp/diff-.env.sample /tmp/diff-.env ; \
	rm /tmp/diff-.env*

.PHONY: distclean
distclean:
	$(COMPOSE) down -v
	rm -rf serve

.PHONY: outdated
outdated:
	$(COMPOSE) run --rm --no-deps --entrypoint /bin/sh app -c "poetry show -o"

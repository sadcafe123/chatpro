SHELL := /bin/bash

# Detect docker compose plugin vs standalone
COMPOSE := $(shell if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then echo "docker compose"; elif command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; else echo "docker compose"; fi)

PROJECT_NAME ?= openwebui-dev
ENV_FILE ?= .env
export COMPOSE_PROJECT_NAME := $(PROJECT_NAME)

.PHONY: help clone up build logs down restart clean pull

help:
	@echo "Targets:"
	@echo "  make clone   - Clone/update open-webui repo locally"
	@echo "  make up      - Build and start OpenWebUI (detached)"
	@echo "  make build   - Build image from local clone"
	@echo "  make logs    - Tail service logs"
	@echo "  make down    - Stop and remove containers"
	@echo "  make restart - Restart service"
	@echo "  make clean   - Down + remove data volume"
	@echo "  make pull    - Update local clone to latest branch"

clone:
	@./scripts/clone-openwebui.sh

up: clone
	$(COMPOSE) --env-file $(ENV_FILE) up -d --build

build:
	$(COMPOSE) --env-file $(ENV_FILE) build

logs:
	$(COMPOSE) logs -f --tail=200 openwebui

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart openwebui

clean: down
	rm -rf openwebui-data

pull: clone
	@true

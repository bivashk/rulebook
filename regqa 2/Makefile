COMPOSE := docker compose

.PHONY: help up down logs migrate fetch test lint fmt psql nuke

help:
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | sed 's/:.*## /  /'

up: ## Build and start db and api in the background
	$(COMPOSE) up -d --build

down: ## Stop containers, keep the data volume
	$(COMPOSE) down

logs: ## Follow api logs
	$(COMPOSE) logs -f api

migrate: ## Apply pending SQL migrations
	uv run python -m regqa.migrate

fetch: ## Crawl the circulars listing
	uv run regqa fetch circulars

test: ## Run the test suite
	uv run pytest -q

lint: ## Check formatting and lint rules
	uv run ruff check .

fmt: ## Apply formatting fixes
	uv run ruff check --fix .

psql: ## Open a psql shell on the database
	$(COMPOSE) exec db psql -U $${POSTGRES_USER:-regqa} -d $${POSTGRES_DB:-regqa}

nuke: ## Stop containers and delete the data volume
	$(COMPOSE) down -v

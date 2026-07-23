.PHONY: help install migrate seed run test lint format check build up down logs clean backup

PYTHON := python
MANAGE := $(PYTHON) manage.py
DOCKER_COMPOSE := docker compose

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

install-pre-commit: ## Install pre-commit hooks
	pre-commit install

migrate: ## Run database migrations
	$(MANAGE) migrate

makemigrations: ## Create new migrations
	$(MANAGE) makemigrations

seed: ## Create test users for all plan tiers
	$(MANAGE) create_test_users

run: ## Start development server
	$(MANAGE) runserver 0.0.0.0:8000

run-celery: ## Start Celery worker
	celery -A config worker -l info

run-celery-beat: ## Start Celery beat scheduler
	celery -A config beat -l info

shell: ## Open Django shell
	$(MANAGE) shell

createsuperuser: ## Create a superuser
	$(MANAGE) createsuperuser

test: ## Run tests with coverage
	pytest tests/ --cov=apps --cov-report=term-missing -v

test-fast: ## Run tests without coverage
	pytest tests/ -x -q

test-urls: ## Run URL accessibility tests
	bash scripts/test_urls.sh http://localhost:8000 team_user testpass123

lint: ## Run linter (ruff)
	ruff check .
	ruff format --check .

format: ## Format code
	ruff check --fix .
	ruff format .

typecheck: ## Run type checker
	mypy apps/ config/

check: lint test ## Run all checks (lint + test)

build: ## Build production Docker image
	$(DOCKER_COMPOSE) build

up: ## Start all services (production)
	$(DOCKER_COMPOSE) --env-file .env up -d

down: ## Stop all services
	$(DOCKER_COMPOSE) down

logs: ## Tail service logs
	$(DOCKER_COMPOSE) logs -f

logs-web: ## Tail web service logs
	$(DOCKER_COMPOSE) logs -f web

ps: ## Show running containers
	$(DOCKER_COMPOSE) ps

db-shell: ## Open psql shell
	$(DOCKER_COMPOSE) exec db psql -U $${DOC_TRANSLATOR_DB_USER:-doctranslator} -d $${DOC_TRANSLATOR_DB_NAME:-doctranslator}

db-backup: ## Backup database
	bash scripts/backup.sh

collectstatic: ## Collect static files
	$(MANAGE) collectstatic --noinput

clean: ## Remove Python cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

docker-clean: ## Remove Docker build cache
	docker system prune -f

# Development (devcontainer)
dev-up: ## Start dev services
	$(DOCKER_COMPOSE) -f .devcontainer/docker-compose.yml up -d

dev-down: ## Stop dev services
	$(DOCKER_COMPOSE) -f .devcontainer/docker-compose.yml down

dev-logs: ## Tail dev service logs
	$(DOCKER_COMPOSE) -f .devcontainer/docker-compose.yml logs -f

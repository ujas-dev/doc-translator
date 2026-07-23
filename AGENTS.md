# AGENTS.md

Instructions for AI coding agents working on this project.

## Project Overview

**Doc Translator** — Django SaaS for document translation with layout preservation.

- **Stack:** Django 5.1 + DRF + Celery + PostgreSQL + Redis + LibreTranslate
- **Python:** 3.12
- **Docker:** 6-service compose (web, celery-worker, celery-beat, db, redis, libretranslate)

## Quick Commands

```bash
# Development
make run                    # Start dev server on :8000
make run-celery             # Start Celery worker
make migrate                # Run migrations
make seed                   # Create test users (free/pro/team/enterprise)

# Testing
make test                   # Run all tests with coverage
make test-fast              # Run tests without coverage (fail fast)
make test-urls              # Run URL accessibility tests

# Code Quality
make lint                   # Ruff lint + format check
make format                 # Auto-fix lint + format
make typecheck              # mypy type checking
make check                  # lint + test (full check)

# Docker
make up                     # Start production services
make down                   # Stop all services
make logs                   # Tail logs
make build                  # Build Docker image
```

## Project Structure

```
config/          # Django project settings, urls, celery, wsgi
apps/            # Django applications
  accounts/      # User auth, profiles, API keys, plan tags
  audit/         # Audit logging
  batch/         # Batch ZIP processing with Celery chords
  billing/       # Stripe integration, plans, subscriptions
  core/          # Dashboard, onboarding, rate limiting, decorators
  documents/     # Document upload, translation, parsers, tasks
  glossaries/    # Glossary CRUD, import/export, term suggestions
  mcp/           # Model Context Protocol API endpoints
  memory/        # Translation memory, fuzzy matching, TMX export
  qa/            # Quality assurance scoring
  status/        # Service health monitoring
  teams/         # Team management, roles, permissions
  translation/   # LibreTranslate, Google, Ollama fallback chain
templates/       # Django HTML templates (43 files)
static/          # CSS, JS assets
tests/           # Pytest test suite (~40 files)
scripts/         # Shell scripts (backup, healthcheck, entrypoint)
sdk/             # Python SDK for API consumption
docs/            # Architecture, market research, integration guides
```

## Key Files

| File | Purpose |
|------|---------|
| `config/settings/base.py` | Django settings (INSTALLED_APPS, middleware, DRF, etc.) |
| `config/settings/dev.py` | Dev overrides (DEBUG=True) |
| `config/settings/prod.py` | Prod overrides (security, Sentry) |
| `config/urls.py` | Root URL routing |
| `config/celery.py` | Celery app configuration |
| `apps/core/decorators.py` | `@plan_required(feature)` decorator |
| `apps/core/middleware.py` | `RateLimitMiddleware` |
| `apps/accounts/models.py` | `UserProfile` with `PLAN_FEATURES` and `has_feature()` |
| `apps/documents/tasks.py` | `process_document` Celery task (full pipeline) |
| `apps/translation/services.py` | Translation fallback chain (LibreTranslate → Google → Ollama) |
| `apps/billing/views.py` | Stripe checkout, portal, webhooks |
| `conftest.py` | Shared pytest fixtures |
| `pytest.ini` | Pytest configuration |
| `pyproject.toml` | Ruff, pytest, mypy, coverage config |

## Conventions

### Code Style
- **Formatter:** Ruff (line length 120)
- **Imports:** isort via Ruff
- **Type hints:** encouraged, mypy with django-stubs
- **No comments** unless asked

### Django Patterns
- Function-based views for HTML pages
- DRF class-based views for API endpoints
- `@login_required` on all authenticated views
- `@plan_required('feature')` for plan-gated views
- Template tags in `apps/accounts/templatetags/plan_tags.py`

### Testing
- Pytest with `pytest-django`
- Fixtures in `conftest.py` (user tiers: free/pro/team/enterprise)
- Tests mirror app structure under `tests/`
- Run `make test` before committing

### Database
- PostgreSQL 16 with pgvector
- All models use `BigAutoField` as default
- Migrations must be committed (never gitignored)
- Test database: separate from dev/prod

### Docker
- Single image for web/celery-worker/celery-beat (different `command`)
- Entrypoint runs migrate + collectstatic on every start
- Redis DB allocation: 0=cache, 1=celery-broker, 2=celery-results

## Test Users

| Username | Plan | Password |
|----------|------|----------|
| `free_user` | free | `testpass123` |
| `free_user2` | free | `testpass123` |
| `pro_user` | pro | `testpass123` |
| `pro_user2` | pro | `testpass123` |
| `team_user` | team | `testpass123` |
| `team_user2` | team | `testpass123` |
| `enterprise_user` | enterprise | `testpass123` |
| `enterprise_user2` | enterprise | `testpass123` |

## Plan Feature Matrix

| Feature | Free | Pro | Team | Enterprise |
|---------|------|-----|------|------------|
| glossary | - | x | x | x |
| tm | - | x | x | x |
| qa | - | x | x | x |
| api_access | - | x | x | x |
| pdf_layout | - | x | x | x |
| batch | - | - | x | x |
| teams | - | - | x | x |
| webhooks | - | - | x | x |
| audit | - | - | x | x |
| sso | - | - | - | x |

## Environment Variables

See `.env.example` for all required variables. Key ones:
- `DJANGO_SECRET_KEY` — session/token signing
- `DATABASE_URL` — PostgreSQL connection
- `REDIS_URL` — Cache backend
- `CELERY_BROKER_URL` — Celery message broker
- `STRIPE_SECRET_KEY` — Stripe payment processing (optional in dev)
- `LIBRETRANSLATE_URL` — LibreTranslate service URL

## Common Tasks

### Adding a new Django app
1. Create `apps/new_app/` with `models.py`, `views.py`, `urls.py`, `apps.py`
2. Add to `INSTALLED_APPS` in `config/settings/base.py`
3. Create migrations: `make makemigrations`
4. Run migrations: `make migrate`
5. Add URL include in `config/urls.py`
6. Add tests in `tests/new_app/`

### Adding a plan-gated feature
1. Add feature name to `PLAN_FEATURES` in `apps/accounts/models.py`
2. Decorate views with `@plan_required('feature_name')`
3. Use `{% has_plan_feature "feature_name" as var %}` in templates
4. Add nav link visibility in `templates/base.html`

### Adding a Celery task
1. Define task in `apps/<app>/tasks.py` with `@shared_task`
2. Autodiscovery handles registration
3. Call with `task_name.delay(args)` or `task_name.apply_async(args, kwargs)`

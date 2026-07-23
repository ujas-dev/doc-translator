# Doc Translator SaaS — Django + Celery + LibreTranslate

A Django-based SaaS for document conversion and translation with a
local-first processing stack. Built on Django + DRF + Celery, with a
self-hosted LibreTranslate sidecar for translation and a Docling-ready
dependency stack (LibreOffice, pandoc, poppler, Tesseract, ffmpeg) for
multi-format parsing and export.

> **Status:** Skeleton. The `DocumentJob` model, REST API endpoints,
> Celery wiring, and `LibreTranslateService` exist, but the Celery task
> `process_document` is a **stub** (`apps/documents/tasks.py` returns
> `{'status': 'queued'}`) and is **not** wired to call
> `LibreTranslateService.translate_text`. See "Known gaps" below.

## Identity

| Field | Value |
|---|---|
| **Compose services (prod)** | 5 total: `web`, `celery-worker`, `celery-beat`, `db`, `redis`, `libretranslate` (6 with LibreTranslate) |
| **Container names** | `doc-translator-web`, `doc-translator-celery-worker`, `doc-translator-celery-beat`, `doc-translator-db`, `doc-translator-redis`, `doc-translator-libretranslate` |
| **Images** | `python:3.12-slim` (built — web/celery-worker/celery-beat share the same image, different `command`) · `pgvector/pgvector:pg16` (db) · `redis:7-alpine` (redis) · `libretranslate/libretranslate:latest` (libretranslate) |
| **Ports** | `${DOC_TRANSLATOR_PORT:-8010}:8000` (web only — others are internal-only) |
| **Memory limits** | web `${DOC_TRANSLATOR_WEB_MEMORY_LIMIT:-2G}` · celery-worker 1G · celery-beat 512M · db 512M · redis 256M · libretranslate 2G (**~4.3 GB total**) |
| **CPU limit** | `${DOC_TRANSLATOR_WEB_CPU_LIMIT:-2.0}` (web only) |
| **Networks** | `doc-translator-internal` (project bridge — all 6) · `backbone` external (only `web` + `celery-worker` join for Ollama/Mem0/Qdrant/n8n/zrok integration) |
| **Restart** | `unless-stopped` for all 6 |
| **Healthcheck** | web: `curl -fsS http://localhost:8000/health/` (30s/10s/3 retries/60s start) · db: `pg_isready` (10s/5s/5 retries/10s start) |
| **Custom entrypoint** | `scripts/entrypoint.sh` — waits for Postgres `pg_isready`, runs `python manage.py migrate --noinput` and `collectstatic --noinput`, then `exec "$@"` |

## Dockerfile

Built from `python:3.12-slim`. A single image is reused for `web`,
`celery-worker`, and `celery-beat` — they differ only by `command`.

| Directive | Purpose |
|---|---|
| `FROM python:3.12-slim` | Base |
| `ENV PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, `DEBIAN_FRONTEND=noninteractive` | Python hygiene |
| `RUN apt-get install …` | `build-essential`, `curl`, `libpq-dev`, `libmagic1`, **`libreoffice`**, **`pandoc`**, **`poppler-utils`**, **`tesseract-ocr`** + `tesseract-ocr-eng` + `tesseract-ocr-hin`, **`ffmpeg`**, `unrtf`, `antiword`, `ca-certificates`, `postgresql-client` (for `pg_isready` in entrypoint) — the document-processing toolchain |
| `WORKDIR /app` | |
| `COPY requirements.txt` + `RUN pip install -r requirements.txt` | Install Python deps before copying app (layer cache) |
| `COPY . /app` | App source |
| `RUN chmod +x /app/scripts/entrypoint.sh /app/scripts/healthcheck.sh` | Make scripts executable |
| `EXPOSE 8000` | Django/gunicorn port |
| `HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 CMD /app/scripts/healthcheck.sh \|\| exit 1` | |
| `ENTRYPOINT ["/app/scripts/entrypoint.sh"]` | Wait-for-PG + migrate + collectstatic |
| `CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "180"]` | Default for `web` service |

### Per-service `command` overrides

| Service | `command` |
|---|---|
| `web` | (inherits CMD) `gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 180` |
| `celery-worker` | `celery -A config worker -l info --concurrency=2` |
| `celery-beat` | `celery -A config beat -l info` |

## docker-compose.yml

### web (Django + gunicorn)

- **`env_file` / `environment`**: see full env table below (compose uses inline `environment:` block, file-level `.env` interpolation)
- **Depends on**: `db` (healthy) · `redis` (started) · `libretranslate` (started)
- **Volumes**: `./media:/app/media` · `./staticfiles:/app/staticfiles`
- **Ports**: `${DOC_TRANSLATOR_PORT:-8010}:8000`
- **Healthcheck**: `curl -fsS http://localhost:8000/health/` — 30s/10s/3 retries/60s start_period
- **Memory**: `${DOC_TRANSLATOR_WEB_MEMORY_LIMIT:-2G}` · **CPU**: `${DOC_TRANSLATOR_WEB_CPU_LIMIT:-2.0}`
- **Networks**: `doc-translator-internal` + `backbone`

### celery-worker

- Same image & most env vars as `web` (no `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`)
- **Command**: `celery -A config worker -l info --concurrency=2`
- **Memory**: 1G
- **Networks**: `doc-translator-internal` + `backbone` (joins backbone to reach Ollama/Mem0/Qdrant if future tasks call them)

### celery-beat

- Same image & subset of env vars (no Ollama/Mem0/Qdrant URLs — beat only schedules)
- **Command**: `celery -A config beat -l info`
- **Memory**: 512M
- **Networks**: `doc-translator-internal` only

### db (Postgres 16 + pgvector)

- **Image**: `pgvector/pgvector:pg16`
- **Env**: `POSTGRES_USER=${DOC_TRANSLATOR_DB_USER:-doctranslator}`, `POSTGRES_PASSWORD=${DOC_TRANSLATOR_DB_PASSWORD:-change_me_doctranslator}`, `POSTGRES_DB=${DOC_TRANSLATOR_DB_NAME:-doctranslator}`, `PGDATA=/var/lib/postgresql/data/pgdata`
- **Volume**: `./data/postgres:/var/lib/postgresql/data/pgdata`
- **Healthcheck**: `pg_isready -U <user> -d <db>` — 10s/5s/5 retries/10s start_period
- **Memory**: 512M
- **Networks**: `doc-translator-internal` only

> **Note:** Doc Translator's db is its OWN Postgres 16 (pgvector-capable).
> It is **not** the shared `core/pgvector` container. Each project/tool
> gets its own Postgres to keep schema migrations isolated.

### redis

- **Image**: `redis:7-alpine`
- **Memory**: 256M
- **Networks**: `doc-translator-internal` only
- **No volume** — Redis is used for 3 separate DBs (cache / Celery broker / Celery result backend); transient loss is acceptable
- **DB allocation**: `redis://redis:6379/0` (cache) · `/1` (Celery broker) · `/2` (Celery result backend)

### libretranslate (translation sidecar)

- **Image**: `libretranslate/libretranslate:latest`
- **Env**: `LT_UPDATE_MODELS=true`, `LT_LOAD_ONLY=${DOC_TRANSLATOR_LT_LOAD_ONLY:-en,fr,de,es,it,hi,ar,pt}`, `LT_API_KEYS=${DOC_TRANSLATOR_LT_API_KEYS:-true}`, `LT_REQ_LIMIT=${DOC_TRANSLATOR_LT_REQ_LIMIT:-100}`, `LT_CHAR_LIMIT=${DOC_TRANSLATOR_LT_CHAR_LIMIT:-5000}`
- **Volume**: `./data/libretranslate:/home/libretranslate/.local` (cached translation models — survives restart)
- **Memory**: 2G (Argos NMT models are large)
- **Networks**: `doc-translator-internal` only
- **No port mapping** — reachable only at `http://libretranslate:5000` from the internal network

## Full environment variable table

File-level `.env` (copy `.env.example` to `.env`). Compose interpolates
these via `${VAR:-default}` in the `environment:` blocks.

| Variable | Default | Use |
|---|---|---|
| `DOC_TRANSLATOR_PORT` | `8010` | Host port → container `:8000` (web) |
| `DOC_TRANSLATOR_SECRET_KEY` | `change_me_secret` | **REQUIRED** — Django session/token signing (rotate: `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `DOC_TRANSLATOR_DB_USER` | `doctranslator` | Postgres role for `db` |
| `DOC_TRANSLATOR_DB_PASSWORD` | `change_me_doctranslator` | **Rotate in repo-root `.env`** |
| `DOC_TRANSLATOR_DB_NAME` | `doctranslator` | Postgres DB name |
| `DOC_TRANSLATOR_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Django `ALLOWED_HOSTS` (comma-separated) |
| `DOC_TRANSLATOR_CSRF_TRUSTED_ORIGINS` | `http://localhost:8010` | Django `CSRF_TRUSTED_ORIGINS` (comma-separated) |
| `DOC_TRANSLATOR_WEB_MEMORY_LIMIT` | `2G` | web container memory cap |
| `DOC_TRANSLATOR_WEB_CPU_LIMIT` | `2.0` | web container CPU cap |
| `DOC_TRANSLATOR_LT_LOAD_ONLY` | `en,fr,de,es,it,hi,ar,pt` | LibreTranslate: comma-separated language codes to load (limits RAM/time on first start). Supported: en, fr, de, es, it, hi, ar, pt, ru, zh, ja, ko |
| `DOC_TRANSLATOR_LT_API_KEYS` | `true` | LibreTranslate: require API key for `/translate` (set `false` in dev) |
| `DOC_TRANSLATOR_LT_REQ_LIMIT` | `100` | LibreTranslate: requests-per-minute-per-IP cap |
| `DOC_TRANSLATOR_LT_CHAR_LIMIT` | `5000` | LibreTranslate: max chars per request |
| `DOC_TRANSLATOR_LIBRETRANSLATE_API_KEY` | (empty) | If `LT_API_KEYS=true`, set this to a key generated via LibreTranslate's `/keys` endpoint; passed as Bearer token to `/translate` |
| `CORE_NETWORK` | `my-stack-backbone` | External backbone network name (for Ollama/Mem0/Qdrant/n8n/zrok integration) |
| `TZ` | `Asia/Kolkata` | Container + log timezone |

### Compose-literal env (in `environment:`, not in `.env`)

| Variable | Value | Use |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` | Selects prod settings (web/worker/beat all use prod) |
| `DEBUG` | `0` | Disable debug in prod |
| `DATABASE_URL` | `postgres://${DOC_TRANSLATOR_DB_USER}:${DOC_TRANSLATOR_DB_PASSWORD}@db:5432/${DOC_TRANSLATOR_DB_NAME}` | Django DB DSN (consumed by `django-environ`) |
| `REDIS_URL` | `redis://redis:6379/0` | Django cache (DB 0) |
| `CELERY_BROKER_URL` | `redis://redis:6379/1` | Celery broker (DB 1) |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/2` | Celery results (DB 2) |
| `LIBRETRANSLATE_URL` | `http://libretranslate:5000` | Internal DNS to sidecar |
| `LIBRETRANSLATE_API_KEY` | `${DOC_TRANSLATOR_LIBRETRANSLATE_API_KEY:-}` | Pass-through from file `.env` |
| `OLLAMA_URL` | `http://ollama:11434` | Backed via backbone DNS — for future LLM-assisted translation |
| `MEM0_URL` | `http://mem0:8000` | Backed via backbone DNS — for future memory-augmented translation |
| `QDRANT_URL` | `http://qdrant:6333` | Backed via backbone DNS — for future vector search |

## API endpoints

Defined in `config/urls.py` and `apps/documents/urls.py`:

| Method | Path | View | Purpose |
|---|---|---|---|
| GET | `/health/` | `config.urls.health` | Liveness probe (returns `{"status": "ok"}`) — used by healthcheck.sh |
| GET | `/admin/` | Django admin | (enabled) |
| GET/POST | `/api/jobs/` | `DocumentJobListCreateView` | List + create document jobs (DRF ListCreateAPIView) |
| GET | `/api/jobs/<id>/` | `DocumentJobRetrieveView` | Retrieve single job status |

### DocumentJob model (`apps/documents/models.py`)

| Field | Type | Notes |
|---|---|---|
| `source_file` | `FileField(upload_to='uploads/')` | Uploaded source document |
| `output_file` | `FileField(upload_to='outputs/', null=True)` | Generated output (read-only via serializer) |
| `source_language` | `CharField(default='auto')` | ISO code or `auto` |
| `target_language` | `CharField(default='en')` | ISO code |
| `source_format` / `target_format` | `CharField(blank=True)` | Format hints (e.g., `pdf`, `docx`) |
| `status` | `CharField` choices: `queued` · `processing` · `translated` · `converted` · `completed` · `failed` | Default `queued`; read-only |
| `error_message` | `TextField(blank=True)` | Populated on failure; read-only |
| `pages` | `IntegerField(default=0)` | Page count; read-only |
| `created_at` / `updated_at` | auto | Read-only |

### Serializer (`apps/documents/serializers.py`)

`DocumentJobSerializer` exposes `__all__` with read-only fields:
`status`, `error_message`, `pages`, `created_at`, `updated_at`,
`output_file`. Client posts `source_file`, `source_language`,
`target_language`, `source_format`, `target_format`.

## Cross-stack integration (via backbone)

| Core service | Integration |
|---|---|
| `core/ollama` | `OLLAMA_URL=http://ollama:11434` — for future LLM-assisted/glossary-aware translation (not wired yet) |
| `core/mem0-aio` | `MEM0_URL=http://mem0:8000` — store/retrieve translation memory per user/tenant (not wired yet) |
| `core/qdrant` | `QDRANT_URL=http://qdrant:6333` — semantic search over translation memory (not wired yet) |
| `core/n8n` | n8n can POST to `http://doc-translator-web:8000/api/jobs/` over backbone DNS to enqueue translation jobs |
| `tools/zrok` | Expose `http://doc-translator-web:8000` publicly via `zrok-agent share public` |

## Known gaps (current skeleton)

| Gap | Location | Impact |
|---|---|---|
| **Celery task is a stub** | `apps/documents/tasks.py`: `process_document(job_id)` returns `{'status': 'queued'}` only — does not process | Jobs stay `queued` forever; no actual translation happens |
| **Service not called** | `LibreTranslateService.translate_text` (in `apps/translation/services.py`) is functional but **never invoked** by the task | Translation logic exists but is dead code in the Celery path |
| **`celery-beat` has no schedule** | `django_celery_beat` is in `INSTALLED_APPS` but no `PeriodicTask`/`Crontab` entries exist | beat runs but schedules nothing |
| **`apps/billing` is empty** | Only `apps.py` + `__init__.py` | No subscription/plan logic |
| **`frontend/`** | Has own README — separate Vite/React shell, not in compose | Not wired to Django |

To make translation functional: in `apps/documents/tasks.py`, replace
the stub body with logic that loads the `DocumentJob`, calls
`LibreTranslateService.translate_text`, and updates `status` through
the lifecycle. See `docs/architecture.md` for the intended pipeline.

## Quick start (production)

```bash
cd projects/doc-translator
cp .env.example .env
# Edit DOC_TRANSLATOR_SECRET_KEY (use python secrets.token_hex(32))
# Edit DOC_TRANSLATOR_DB_PASSWORD

# Start your core stack first (for backbone network)
docker compose --env-file ../../.env up -d --build

# First run: entrypoint auto-runs migrate + collectstatic
open http://localhost:8010/health/    # expect {"status":"ok"}
open http://localhost:8010/admin/     # create superuser: docker compose exec web python manage.py createsuperuser
```

### Development (VS Code Dev Container)

A separate `.devcontainer/docker-compose.yml` runs:
`doc-translator-app-dev` (debugpy on `:5678`, port `:8000`, `command: sleep infinity`),
`doc-translator-db-dev` (pgvector:pg16, port `:5434`),
`doc-translator-redis-dev` (port `:6379`),
`doc-translator-libretranslate-dev` (port `:5001`).

Dev uses `DJANGO_SETTINGS_MODULE=config.settings.dev`, `DEBUG=1`, and
hardcoded dev credentials (`doctranslator:doctranslator`). Dev data
lives in `data/dev/` (separate from prod `data/postgres/`).

1. Open folder in VS Code → "Reopen in Container"
2. `python manage.py migrate`
3. `python manage.py runserver 0.0.0.0:8000`
4. Start Celery worker if testing jobs: `celery -A config worker -l info`

## File structure

| Path | Purpose |
|---|---|
| `Dockerfile` | Production image (python:3.12-slim + doc toolchain + gunicorn) |
| `docker-compose.yml` | 6-service prod compose |
| `.devcontainer/Dockerfile` + `.devcontainer/docker-compose.yml` | Dev container (debugpy, Node 20, sleep infinity) |
| `.env.example` | File-level env template (16 keys) |
| `scripts/entrypoint.sh` | Wait-for-PG + migrate + collectstatic + `exec "$@"` |
| `scripts/healthcheck.sh` | `curl -fsS http://localhost:8000/health/` |
| `scripts/dev-post-create.sh` | Dev container post-create hook |
| `requirements.txt` | Python deps (Django, DRF, drf-spectacular, celery, redis, django-environ, django-celery-beat, django-celery-results, whitenoise, pymysql/psycopg2) |
| `config/` | Django project (settings, urls, wsgi, asgi, celery) — `config/settings/{base,dev,prod}.py` |
| `config/celery.py` | Celery app: `app = Celery('doc_translator')`, `autodiscover_tasks()` |
| `apps/core/` | Root API includes (health, etc.) |
| `apps/documents/` | DocumentJob model, DRF views, serializer, **stubbed tasks.py** |
| `apps/translation/` | `LibreTranslateService` (functional, not wired to task) |
| `apps/billing/` | Empty placeholder |
| `frontend/` | Separate Vite/React shell (own README, not in compose) |
| `docs/architecture.md` | Intended processing pipeline design |
| `docs/stack-integration.md` | Integration guide for Ollama/Mem0/Qdrant/n8n/zrok |
| `docs/market-research.md` | Product differentiation notes |
| `data/postgres/` | Prod PGDATA (bind mount) |
| `data/libretranslate/` | LibreTranslate model cache (bind mount) |
| `media/` | Uploaded source files + generated outputs |
| `staticfiles/` | `collectstatic` output |

## Persistence & backups

| Resource | Bind mount |
|---|---|
| Postgres | `./data/postgres/` |
| LibreTranslate models | `./data/libretranslate/` |
| Uploads + outputs | `./media/` |
| Static files | `./staticfiles/` |

```bash
cd projects/doc-translator
docker exec doc-translator-db pg_dump -U "$DOC_TRANSLATOR_DB_USER" -d "$DOC_TRANSLATOR_DB_NAME" > ../../backups/doc-translator-$(date +%Y%m%d).sql

# Media (uploads + outputs)
tar -czf ../../backups/doc-translator-media-$(date +%Y%m%d).tar.gz media/
```

## Operational notes

- **Single image, three roles** — `web`, `celery-worker`, `celery-beat` share one built image; only `command` differs. Rebuilding once updates all three: `docker compose --env-file ../../.env up -d --build`.
- **Entry always migrates** — `scripts/entrypoint.sh` runs `migrate --noinput` + `collectstatic --noinput` on every web/worker/beat start (idempotent).
- **Redis DB allocation** — DB 0 (Django cache), DB 1 (Celery broker), DB 2 (Celery results). Do not collapse these; Celery broker and results must stay separate.
- **LibreTranslate first start is slow** — `LT_UPDATE_MODELS=true` downloads Argos NMT models on first boot (several minutes depending on `LT_LOAD_ONLY`). The `./data/libretranslate/` volume caches them for subsequent starts.
- **`LT_API_KEYS=true` in prod** — without a key, all `/translate` calls 403. Generate a key from inside the container: `docker compose exec libretranslate libretranslate --api-keys-gen` then set `DOC_TRANSLATOR_LIBRETRANSLATE_API_KEY` and recreate.
- **Doc toolchain is heavy** — LibreOffice + pandoc + poppler + Tesseract add ~500 MB to the image; this is intentional (Docling-ready). The image is ~1.2 GB built.
- **Memory budget**: web 2G + celery-worker 1G + celery-beat 512M + db 512M + redis 256M + libretranslate 2G = **~4.3 GB**. Keep stopped when not actively developing.

## Deep docs

- `docs/architecture.md` — intended document processing pipeline
- `docs/stack-integration.md` — Ollama/Mem0/Qdrant/n8n/zrok integration recipes
- `docs/market-research.md` — product differentiation notes
- Upstream Django: https://docs.djangoproject.com
- Upstream Celery: https://docs.celeryq.dev
- Upstream LibreTranslate: https://github.com/LibreTranslate/LibreTranslate

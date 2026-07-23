# Existing stack integration

## Recommended repo placement

Place this project under:

`my-stack/projects/doc-translator/`

This keeps it isolated from shared infrastructure while still allowing it to connect to the shared backbone network [cite:100][cite:101].

## How it uses your stack

- **Ollama** at `http://ollama:11434` for AI post-editing, summarization, glossary normalization, and style harmonization.
- **Mem0** at `http://mem0:8000` for persistent customer preferences, glossary memory, and repeated phrase handling.
- **Qdrant** at `http://qdrant:6333` for semantic retrieval of past translations, translation memory chunks, and review examples.
- **n8n** through the backbone network for ingestion and export automations.
- **zrok** to expose a staging instance or customer demo link publicly when needed.

## Isolation rule

Use a **dedicated PostgreSQL and Redis** for this SaaS project, not the shared core Postgres, because product data should stay isolated even if the stack tools share infra [cite:101].

## zrok exposure

The zrok agent auto-discovers HTTP services on the backbone network — just attach this project's `web` service to `backbone` and it gets tunneled automatically within the poll interval.

For ad-hoc manual exposure:
```bash
docker compose exec zrok-agent zrok2 share public http://doc-translator-web:8000
```

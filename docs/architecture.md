# Architecture

## Core services

- Django web app for auth, UI, API, billing hooks, and job orchestration.
- Celery worker for document processing, OCR, translation, conversion, and exports.
- Celery beat for scheduled cleanup, retry, quota reset, and housekeeping.
- PostgreSQL for application data.
- Redis for task queue and caching.
- LibreTranslate for self-hosted machine translation [web:673].
- Docling for structure-aware parsing and export across many formats [page:2].
- LibreOffice, Pandoc, Poppler, Tesseract, and FFmpeg for conversion and OCR pipeline support.

## Why this stack fits

Docling supports a wide range of input formats including PDF, DOCX, XLSX, PPTX, ODT, EPUB, Markdown, HTML, CSV, images, audio, and video, and can export to HTML, Markdown, JSON, text, Doctags, and WebVTT [page:2]. That makes it a strong base for a format-flexible SaaS rather than writing separate parsers for every format [page:2].

LibreTranslate gives you a self-hosted translation API with endpoints for translation and language handling, which keeps private documents off third-party platforms [web:673].

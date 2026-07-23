# Changelog

All notable changes to Doc Translator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Plan-based feature gating with `@plan_required` decorator
- Onboarding wizard with plan-aware step flow
- Pricing page with Stripe checkout integration
- Dev-mode billing fallback (no Stripe keys required)
- Rate limiting middleware (per-plan, per-API-key, per-IP)
- API docs link in footer pointing to Swagger UI
- Test user management command (`create_test_users`)
- Python SDK for API consumption
- MCP (Model Context Protocol) API endpoints
- Team management with role-based permissions
- Audit logging system
- Quality assurance scoring (length, term, untranslated detection)
- Batch processing with ZIP upload and Celery chord orchestration
- Translation memory with fuzzy matching and TMX export
- Glossary system with CSV import, TBX/XLIFF export
- PDF layout preservation with formula detection
- DOCX layout preservation
- Bilingual output (side-by-side source/translation)
- Multi-format document parsing (TXT, DOCX, PDF, CSV, XLSX, PPTX, HTML, MD, images)
- OCR support via Tesseract
- Service status monitoring dashboard
- Multi-tier billing (Free, Pro, Team, Enterprise)
- Dark mode UI support
- HTMX-based live status polling
- CI/CD pipeline (GitHub Actions: lint, test, Docker build)
- Dev Container setup with debugpy support
- Comprehensive test suite (~40 test files)
- Swagger/ReDoc/OpenAPI documentation

### Changed
- Upgraded to Django 5.1.15
- Migrated from SQLite to PostgreSQL (pgvector) in production
- Celery task `process_document` fully implemented (no longer a stub)

### Fixed
- Login page TemplateSyntaxError (removed socialaccount dependency)
- Logout endpoint (POST form with CSRF token)
- Email-based login fallback
- Onboarding skip link (marks onboarding complete before redirect)
- Onboarding glossary step (skipped for free users)
- Pricing buttons (dev-mode fallback when Stripe not configured)
- API docs link (Swagger UI instead of raw YAML download)
- Batch models and views
- Memory views and services
- QA and audit migrations
- Document parsers (DOCX diff, PDF formula detection)
- URL test script (bash arithmetic, CSRF extraction, 429 tolerance)

## [0.1.0] - 2026-07-23

### Added
- Initial project structure
- Docker Compose setup (6 services)
- Django project configuration
- REST API framework (DRF)
- Celery task queue setup
- LibreTranslate integration
- Basic document upload and processing

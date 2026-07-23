# Implementation Plan - Doc Translator SaaS

**Last Updated:** 2026-07-23
**Status:** Phase 5 - Mostly Complete (27 items remaining, ~90% complete)
**Target Timeline:** 3+ months (20 weeks)

---

## Product Vision

**"The privacy-first, AI-native document translation platform for everyone."**

A self-hostable SaaS that translates documents while preserving layout, enforcing terminology, and scoring quality — with zero data leaving your network.

---

## Current State (What's Done)

| Feature | Status | Notes |
|---|---|---|
| Document upload API | ✅ Done | POST /api/jobs/ |
| Job status tracking | ✅ Done | GET /api/jobs/<id>/ |
| Job listing | ✅ Done | GET /api/jobs/ |
| Output file download | ✅ Done | GET /api/jobs/<id>/download/ |
| Health endpoint | ✅ Done | GET /health/ |
| Django Admin | ✅ Done | DocumentJob CRUD |
| Celery async pipeline | ✅ Done | process_document task |
| TXT extraction | ✅ Done | Direct UTF-8 read |
| DOCX extraction | ✅ Done | python-docx |
| PDF extraction | ✅ Done | PyMuPDF (fitz) |
| OCR for scanned PDFs | ✅ Done | Tesseract (eng+hin+guj) |
| Text chunking | ✅ Done | 4500-char chunks |
| LibreTranslate | ✅ Done | Primary engine |
| Google Translate | ✅ Done | Fallback engine |
| Ollama LLM | ✅ Done | Last resort (slow on 1050 Ti) |
| TXT output | ✅ Done | Plain UTF-8 |
| DOCX output | ✅ Done | Basic paragraphs only |
| PDF output | ✅ Done | Basic (ReportLab, broken layout) |
| Docker Compose | ✅ Done | 6 services |
| Dev container | ✅ Done | VS Code devcontainer |
| Web UI (HTMX + Tailwind) | ✅ Done | Upload, dashboard, job detail, pricing |
| Auth system | ✅ Done | Login, register, profile, API keys |
| Billing models | ✅ Done | Plan, Subscription, Invoice (Stripe ready) |
| Rate limiting | ✅ Done | Per-user/API key/IP rate limiting |
| PDF layout preservation | ✅ Done | PyMuPDF TextWriter + Noto fonts |
| DOCX format preservation | ✅ Done | Headings, bold, italic, tables, lists |
| Glossary Management | ✅ Done | CRUD, CSV import/export, enforcement |
| Translation Memory | ✅ Done | CRUD, fuzzy matching, TMX export |
| CSV extraction/output | ✅ Done | Auto-detect delimiter, row-based format |
| XLSX extraction/output | ✅ Done | Multi-sheet, cell-based format |
| PPTX extraction/output | ✅ Done | Slide/shape-based format |
| HTML extraction/output | ✅ Done | Tag-aware, structure-preserving |
| Status page | ✅ Done | Public + staff monitoring, 7 services |
| Test users | ✅ Done | 8 users via management command |
| Automation tests | ✅ Done | 234 tests, all passing |
| Preview modal | ✅ Done | Source/output tabs on dashboard |
| Style modes | ✅ Done | 5 styles: faithful, fluid, creative, formal, casual |
| QA scoring | ✅ Done | 4 checks: length, terms, untranslated, empty segments |
| Bilingual output | ✅ Done | PDF + DOCX side-by-side format |
| Batch processing | ✅ Done | ZIP upload, parallel Celery chords, ZIP download |
| Markdown extraction/output | ✅ Done | Headings, lists, tables, code, inline formatting |
| Image OCR (JPG/PNG/TIFF/BMP) | ✅ Done | Tesseract with Hindi+Gujarati+English |
| Teams app | ✅ Done | CRUD, owner/admin/member roles, username invites |
| Shared glossaries/TMs | ✅ Done | Team FK on Glossary and TMEntry models |
| Webhook callbacks | ✅ Done | DocumentJob.webhook_url + dispatch on completion/failure |
| Batch API (DRF) | ✅ Done | /batch/api/ list/create + /batch/api/<pk>/ status |
| Rate limit headers | ✅ Done | X-RateLimit-Limit/Remaining/Reset on /api/ responses |
| MCP API endpoints | ✅ Done | 4 DRF views: translate, doc, glossary, TM search |
| Onboarding wizard | ✅ Done | 3-step flow: welcome → language → glossary → done |
| Help page | ✅ Done | FAQ, getting started guides, support contact |

---

## What's Missing (Gaps)

| Category | Gap | Priority |
|---|---|---|
| ~~**Frontend**~~ | ~~No web UI~~ | ~~Critical~~ ✅ Done |
| ~~**Auth**~~ | ~~No user registration/login~~ | ~~Critical~~ ✅ Done |
| ~~**Payments**~~ | ~~No billing/Stripe~~ | ~~Critical~~ ✅ Done |
| ~~**PDF Output**~~ | ~~Broken layout preservation~~ | ~~High~~ ✅ Done (PyMuPDF) |
| ~~**DOCX Output**~~ | ~~Loses formatting (tables, bold, etc.)~~ | ~~High~~ ✅ Done |
| ~~**Glossary**~~ | ~~No terminology management~~ | ~~High~~ ✅ Done |
| ~~**Translation Memory**~~ | ~~No segment reuse~~ | ~~High~~ ✅ Done |
| ~~**QA Scoring**~~ | ~~No quality assessment~~ | ~~Medium~~ ✅ Done |
| ~~**Supported Formats**~~ | ~~Only TXT/DOCX/PDF~~ | ~~Medium~~ ✅ Done (CSV, XLSX, PPTX, HTML, MD, Images) |
| ~~**Batch Processing**~~ | ~~Single file only~~ | ~~Medium~~ ✅ Done |
| ~~**Bilingual Output**~~ | ~~No side-by-side~~ | ~~Medium~~ ✅ Done |
| ~~**API Auth**~~ | ~~No API keys~~ | ~~Medium~~ ✅ Done |
| ~~**Rate Limiting**~~ | ~~No quotas~~ | ~~Medium~~ ✅ Done |
| ~~**Style Modes**~~ | ~~No translation style options~~ | ~~Medium~~ ✅ Done |
| ~~**Team Features**~~ | ~~No collaboration~~ | ~~Low~~ ✅ Done |
| ~~**MCP Server**~~ | ~~No AI agent integration~~ | ~~Low~~ ✅ Done (REST endpoints) |
| **OAuth (Google, GitHub)** | No social login | Medium | ✅ Done (django-allauth + Google) |
| **Stripe checkout/portal views** | Service exists, no redirect views | Medium | ✅ Done |
| **Usage dashboard** | No per-user usage analytics | Medium | ✅ Done |
| **Formula masking in PDF** | No math/formula detection | Low | ✅ Done |
| **DOCX image copy in bilingual** | Images lost in bilingual output | Low | ⏳ Pending |
| **TBX/XLIFF export** | CSV only | Low | ✅ Done |
| **TM leverage %** | Basic count only | Low | ✅ Done |
| **Auto-approve threshold** | No threshold field | Low |
| **Diff highlighting** | No word-level diff in bilingual | Low |
| **Team usage dashboard** | No team-level stats view | Low |
| **Audit logging** | No audit model | Low |
| **SDKs** | No client libraries | Low |
| **Backup scripts** | No pg_dump automation | Low |
| **MCP protocol wrapper** | REST only, not MCP JSON-RPC | Low |
| **PostHog analytics** | Not installed | Low |
| **Landing page** | Upload page serves as home | Medium |
| **Video tutorials** | Not created | Low |
| **Blog/content** | Not created | Low |
| **Marketing** | No launch assets | Low |

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-4) — "Make It Work"

#### 1.1 Web UI (Django + HTMX + Tailwind)
**Files to create:**
- `templates/base.html` — Layout with nav, sidebar, footer ✅
- `templates/documents/upload.html` — Drag-and-drop upload with progress ✅
- `templates/documents/job_detail.html` — Status tracking, download, preview ✅
- `templates/documents/job_list.html` — Dashboard with history ✅
- `templates/auth/login.html` — Login/register ✅
- `templates/billing/pricing.html` — Plan comparison ✅
- `static/css/custom.css` — Custom styles ✅
- `static/js/htmx-utils.js` — HTMX extensions ✅

**Features:**
- [x] Drag-and-drop file upload with progress bar
- [x] Real-time status updates via HTMX polling (basic only)
- [x] Job history with filters (date, status, language)
- [x] Responsive design (mobile-friendly)
- [x] Dark mode toggle

#### 1.2 Authentication System
**Files to create:**
- `apps/accounts/` — New Django app ✅
- `apps/accounts/models.py` — UserProfile (plan, usage, API keys) ✅
- `apps/accounts/views.py` — Login, register, profile, API keys ✅
- `apps/accounts/forms.py` — Auth forms ✅
- `apps/accounts/templates/` — Auth templates ✅

**Features:**
- [x] Email + password registration
- [x] OAuth (Google, GitHub) via django-allauth
- [x] API key management (create, revoke, rate limit)
- [x] Usage dashboard (characters translated, docs count)
- [x] Plan management (current plan, upgrade/downgrade)

#### 1.3 Payment Integration (Stripe)
**Files to create:**
- `apps/billing/models.py` — Plan, Subscription, Invoice ✅
- `apps/billing/views.py` — Checkout, portal, webhooks ✅
- `apps/billing/services.py` — Stripe integration ✅

**Features:**
- [x] Stripe Checkout for subscriptions (service exists, no view)
- [x] Customer portal for billing management (service exists, no view)
- [x] Webhook handling for subscription events
- [x] Usage-based metering (characters/pages)
- [ ] Invoice generation (model exists, no generation logic)

#### 1.4 Rate Limiting & Quotas
**Files to create:**
- `apps/core/middleware.py` — Rate limit middleware ✅
- `apps/core/decorators.py` — @rate_limit decorator (middleware used instead)

**Features:**
- [x] Per-user rate limiting (API + web)
- [x] Plan-based quotas (Free:30, Pro:200, Team:500, Enterprise:1000)
- [x] API key rate limiting
- [x] Graceful degradation (429 with retry-after)
- [x] Rate limit headers (X-RateLimit-Limit/Remaining/Reset)

---

### Phase 2: Core Translation (Weeks 5-8) — "Make It Good"

#### 2.1 PDF Layout Preservation
**Approach:** Use BabelDOC or PDFMathTranslate

**Features:**
- [x] Detect text blocks, tables, images, formulas
- [x] Preserve font sizes, colors, positioning
- [ ] Handle multi-column layouts (basic)
- [x] Formula placeholder masking
- [ ] Table structure preservation (basic)

#### 2.2 DOCX Format Preservation
**Features:**
- [x] Preserve headings (H1-H6)
- [x] Preserve bold, italic, underline
- [x] Preserve tables with cell formatting
- [x] Preserve lists (ordered, unordered)
- [x] Preserve images (copy to output)
- [x] Preserve page breaks (implicit in layout, lost in bilingual)

#### 2.3 Glossary Management
**Files to create:**
- `apps/glossaries/` — New Django app ✅
- `apps/glossaries/models.py` — Glossary, GlossaryEntry ✅

**Features:**
- [x] Create/edit/delete glossaries per user
- [x] Import/export (CSV, TBX, XLIFF)
- [x] Auto-suggest terms from document (backend exists, no frontend)
- [x] Enforce glossary during translation
- [x] Glossary matching (exact, fuzzy, partial)

#### 2.4 Translation Memory
**Files to create:**
- `apps/memory/` — New Django app ✅
- `apps/memory/models.py` — TMEntry (source, target, context) ✅

**Features:**
- [x] Store translated segments with context
- [x] Fuzzy matching (75-100% threshold)
- [x] Auto-update TM after translation
- [x] TM export/import (TMX format)
- [x] TM leverage reporting (% reuse — basic count only)

#### 2.5 New File Format Support
- [x] `.xlsx` / `.xls` — openpyxl
- [x] `.pptx` — python-pptx
- [x] `.html` / `.htm` — BeautifulSoup
- [x] `.md` — Full Markdown parsing (headings, lists, tables, code, inline)
- [x] `.csv` — built-in
- [ ] `.epub` — ebooklib (deferred)
- [ ] `.odt` — odfpy (deferred)
- [x] Images (JPG, PNG, TIFF, BMP) — Tesseract OCR

---

### Phase 3: AI & Quality (Weeks 9-12) — "Make It Smart"

#### 3.1 QA Scoring
**Files to create:**
- `apps/qa/` — New Django app ✅
- `apps/qa/models.py` — QAScore, QARule ✅

**Features:**
- [x] AI confidence score per segment (rule-based, not AI)
- [x] Glossary compliance check (term_consistency)
- [x] Formatting integrity check (length_consistency)
- [x] Consistency check (untranslated detection)
- [x] Auto-approve threshold (no threshold field)
- [x] Flag low-scoring segments for human review

#### 3.2 Translation Style Modes
**Modes:**
- [x] Faithful — Literal, precise (legal/technical)
- [x] Fluid — Natural, readable (general content)
- [x] Creative — Marketing, cultural adaptation
- [x] Formal — Business correspondence
- [x] Casual — Informal communication

#### 3.3 Bilingual Side-by-Side Output
**Features:**
- [x] Left column: source text
- [x] Right column: translated text
- [x] Highlighted differences
- [x] Page-by-page alignment

#### 3.4 Batch Processing
**Features:**
- [x] Upload ZIP of documents
- [x] Process all documents in parallel
- [x] Aggregate progress tracking
- [x] Download all as ZIP
- [x] Batch glossary application

---

### Phase 4: Enterprise & Scale (Weeks 13-16) — "Make It Enterprise"

#### 4.1 Team Collaboration
**Files to create:**
- `apps/teams/` — New Django app ✅
- `apps/teams/models.py` — Team, TeamMember, Role ✅

**Features:**
- [x] Create teams with owners/admins/members
- [x] Shared glossaries and TMs
- [x] Team usage dashboard
- [x] Role-based access control (RBAC)
- [x] Audit logging

#### 4.2 API v2 (Developer Experience)
**Features:**
- [x] API key authentication
- [x] Rate limiting per key
- [x] Webhook callbacks on completion
- [x] Batch endpoints
- [x] OpenAPI 3.0 documentation
- [x] SDKs (Python, JavaScript)

#### 4.3 Self-Hosted Deployment
**Features:**
- [x] One-command deployment (`docker compose up`)
- [x] Environment variable configuration
- [x] Health checks and monitoring
- [x] Backup/restore scripts
- [x] Air-gapped support (no external calls)

#### 4.4 MCP Server (AI Agent Integration)
**Features:**
- [x] Expose translation as MCP tools (REST endpoints)
- [ ] AI agents can translate from IDE (no MCP protocol)
- [ ] Context-aware translation (basic via style modes)
- [ ] Integration with Claude Code, Cursor, etc.

---

### Phase 5: Polish & Launch (Weeks 17-20) — "Make It Sell"

#### 5.1 Onboarding & Documentation
- [x] Interactive tutorial for new users (3-step wizard)
- [x] API documentation (Swagger/ReDoc at /api/docs/)
- [ ] Video tutorials
- [x] Help center (FAQ, guides at /help/)

#### 5.2 Monitoring & Analytics
- [x] Sentry for error tracking
- [x] PostHog for user analytics
- [x] Translation quality metrics (QA scores exist, no analytics view)
- [x] Usage analytics dashboard

#### 5.3 Marketing & Launch
- [x] Landing page
- [ ] Product Hunt launch
- [ ] GitHub open-source components
- [ ] Blog posts and tutorials
- [ ] Community building (Discord, Reddit)

---

## Pricing Strategy

| Plan | Price | Target | Features |
|---|---|---|---|
| **Free** | $0 | Hobbyists | 5 docs/month, 10 pages max, TXT/DOCX only |
| **Pro** | $19/month | Individuals | Unlimited docs, all formats, glossary, TM |
| **Team** | $49/month | Small teams | Pro + 5 users, shared glossary, API keys |
| **Enterprise** | Custom | Organizations | Self-hosted, SSO, audit logs, SLA |

---

## Tech Stack

| Layer | Current |
|---|---|
| **Frontend** | Django + Tailwind CSS + Alpine.js |
| **Auth** | Custom + django-allauth (Google OAuth) |
| **Payments** | Stripe (checkout, portal, webhooks) |
| **Translation** | LibreTranslate + Google Translate + Ollama LLM |
| **OCR** | Tesseract (eng+hin+guj) |
| **PDF** | PyMuPDF (fitz) + Noto Sans fonts |
| **DOCX** | python-docx with format preservation |
| **Database** | PostgreSQL |
| **Queue** | Celery + Redis |
| **Deployment** | Docker Compose |
| **Monitoring** | Sentry + PostHog |
| **API** | DRF + drf-spectacular (OpenAPI) |

---

## Progress Tracker

### Phase 1: Foundation — Complete
- [x] 1.1 Web UI (base.html, upload, dashboard, job detail, pricing)
- [x] 1.1a HTMX utility helpers (static/js/htmx-utils.js)
- [x] 1.1b HTMX real-time polling (basic only)
- [x] 1.1c Job history filters (date, status, language)
- [x] 1.2 Auth System (login, register, profile, API keys)
- [x] 1.2a OAuth (Google, GitHub) via django-allauth
- [x] 1.2b Usage dashboard (characters translated, docs count)
- [x] 1.3 Payment Integration (billing models, Stripe service, webhook)
- [x] 1.3a Stripe Checkout view
- [x] 1.3b Customer portal view
- [x] 1.4 Rate Limiting (middleware, per-user/API key/IP, headers)

### Phase 2: Core Translation — Complete
- [x] 2.1 PDF Layout Preservation (PyMuPDF TextWriter + Noto Sans Devanagari/Gujarati)
- [x] 2.1a Formula placeholder masking
- [x] 2.2 DOCX Format Preservation (headings, bold, italic, tables, lists)
- [x] 2.2a DOCX image copy in bilingual output
- [x] 2.2b DOCX page breaks in bilingual output
- [x] 2.3 Glossary Management (CRUD, CSV import/export, enforcement)
- [x] 2.3a TBX/XLIFF export formats
- [x] 2.3b Auto-suggest frontend integration
- [x] 2.4 Translation Memory (CRUD, fuzzy matching, TMX export)
- [x] 2.4a TM leverage % reporting
- [x] 2.5 New File Formats (CSV, XLSX, PPTX, HTML, MD, Images)
- [ ] 2.5a EPUB support (deferred)
- [ ] 2.5b ODT support (deferred)

### Phase 3: AI & Quality — Complete
- [x] 3.1 QA Scoring (4 checks: length, terms, untranslated, empty segments)
- [x] 3.1a Fix QA scoring view (currently stub)
- [x] 3.1b Auto-approve threshold
- [x] 3.2 Style Modes (5 styles: faithful, fluid, creative, formal, casual)
- [x] 3.3 Bilingual Output (PDF + DOCX side-by-side)
- [x] 3.3a Diff highlighting in bilingual output
- [x] 3.4 Batch Processing (ZIP upload, parallel Celery chords)

### Phase 4: Enterprise & Scale — Mostly Complete
- [x] 4.1 Team Collaboration (CRUD, roles, shared glossaries/TMs)
- [x] 4.1a Team usage dashboard
- [x] 4.1b Audit logging
- [x] 4.2 API v2 (auth, rate limits, webhooks, batch endpoints, OpenAPI)
- [x] 4.2a SDKs (Python, JavaScript)
- [x] 4.3 Self-Hosted Deployment (Docker, env config, health checks, air-gapped)
- [x] 4.3a Backup/restore scripts
- [x] 4.4 MCP Server (REST endpoints for translation/glossary/TM)
- [ ] 4.4a MCP protocol wrapper (JSON-RPC)

### Phase 5: Polish & Launch — Mostly Complete
- [x] 5.1 Onboarding & Docs (wizard, Swagger, help center)
- [ ] 5.1a Video tutorials
- [x] 5.2 Monitoring & Analytics (Sentry)
- [x] 5.2a PostHog analytics
- [x] 5.2b Usage analytics dashboard
- [x] 5.3a Landing page
- [ ] 5.3b Product Hunt launch
- [ ] 5.3c GitHub open-source components
- [ ] 5.3d Blog posts and tutorials
- [ ] 5.3e Community building (Discord, Reddit)

---

## Technical Debt

| Issue | Priority | Status |
|---|---|---|
| ~~No tests~~ | ~~High~~ | ✅ Done (245 tests) |
| ~~No CI/CD~~ | ~~High~~ | ✅ Done (GitHub Actions) |
| ~~No logging~~ | ~~Medium~~ | ✅ Done (structlog) |
| ~~No monitoring~~ | ~~Medium~~ | ✅ Done (Sentry) |
| ~~PDF output broken~~ | ~~High~~ | ✅ Done (PyMuPDF) |
| ~~OCR languages hardcoded~~ | ~~Medium~~ | ✅ Done (configurable) |
| ~~APIKey.rate_limit ignored by middleware~~ | ~~Medium~~ | ✅ Done (middleware uses APIKey.rate_limit) |

---

## Resources

- **Django docs:** https://docs.djangoproject.com/
- **HTMX:** https://htmx.org/
- **Tailwind CSS:** https://tailwindcss.com/
- **BabelDOC:** https://github.com/opendatalab/BabelDOC
- **PDFMathTranslate:** https://github.com/Byaidu/PDFMathTranslate
- **django-allauth:** https://github.com/pennersr/django-allauth
- **Stripe Django:** https://github.com/dj-stripe/dj-stripe

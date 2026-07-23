# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in Doc Translator, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

### How to Report

1. Email: **security@doctranslator.com** (or create a private GitHub advisory)
2. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment** within 48 hours
- **Assessment** within 1 week
- **Fix timeline** communicated based on severity
- **Credit** in the release notes (unless you prefer anonymity)

## Security Measures

### Authentication
- Password hashing via Django's PBKDF2
- CSRF protection on all forms
- Session-based authentication with secure cookies
- API key authentication with rate limiting

### Authorization
- Plan-based feature gating
- Per-user resource isolation
- Role-based team permissions (owner/admin/member)

### Infrastructure
- Environment variables for all secrets (never committed)
- HTTPS enforcement in production
- Security headers (HSTS, XSS filter, content-type nosniff)
- Rate limiting per user/plan/API key/IP

### Data
- Database encryption at rest (PostgreSQL)
- File uploads stored with restricted permissions
- Automatic cleanup of expired sessions

## Best Practices for Deployment

1. Use strong, unique `SECRET_KEY`
2. Enable `SECURE_SSL_REDIRECT` in production
3. Set `CSRF_COOKIE_SECURE = True`
4. Set `SESSION_COOKIE_SECURE = True`
5. Keep dependencies updated (`pip-audit`)
6. Use environment-specific settings (`config.settings.prod`)
7. Enable Sentry error tracking
8. Regular database backups

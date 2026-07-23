# Contributing to Doc Translator

Thank you for your interest in contributing to Doc Translator! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/your-username/doc-translator.git`
3. **Create** a feature branch: `git checkout -b feature/your-feature`
4. **Set up** development environment:
   ```bash
   make install
   make install-pre-commit
   cp .env.example .env
   make migrate
   make seed
   ```

## Development Workflow

### Code Style

- **Formatter/Linter:** Ruff (configured in `pyproject.toml`)
- **Type Checking:** mypy with django-stubs
- **Line Length:** 120 characters max
- **Indentation:** 4 spaces for Python, 2 spaces for HTML/JS/CSS

Run before committing:
```bash
make check   # lint + test
```

Or manually:
```bash
ruff check .        # lint
ruff format .       # format
pytest tests/       # test
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:
- Trailing whitespace removal
- Ruff lint + format check
- mypy type check
- YAML/TOML validation

Install: `make install-pre-commit`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add bilingual DOCX export
fix: handle empty glossary in translation
docs: update API documentation
refactor: extract translation service
test: add batch processing tests
chore: update dependencies
```

### Branch Naming

- `feature/description` — new features
- `fix/description` — bug fixes
- `docs/description` — documentation
- `refactor/description` — code refactoring
- `test/description` — test additions

## Pull Request Process

1. **Update** documentation if adding/changing features
2. **Add** tests for new functionality
3. **Ensure** all checks pass: `make check`
4. **Fill out** the PR template completely
5. **Request** a review from maintainers

### PR Requirements

- [ ] Tests pass (`make test`)
- [ ] Linting passes (`make lint`)
- [ ] No type errors (`make typecheck`)
- [ ] Documentation updated (if applicable)
- [ ] Changelog entry added (if applicable)

## Reporting Issues

- Use GitHub Issues with appropriate templates
- Include reproduction steps
- Include environment details (OS, Python version, Docker version)
- For security issues, see [SECURITY.md](SECURITY.md)

## Code of Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Questions?

Open a GitHub Discussion or reach out to the maintainers.

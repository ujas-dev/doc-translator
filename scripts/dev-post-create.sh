#!/usr/bin/env bash
set -e

echo "=== Doc Translator Dev Container Setup ==="

until pg_isready -h db-dev -p 5432 -U doctranslator >/dev/null 2>&1; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

echo "PostgreSQL ready."
python manage.py migrate || true

echo ""
echo "Useful commands:"
echo "  python manage.py migrate"
echo "  python manage.py createsuperuser"
echo "  python manage.py runserver 0.0.0.0:8000"
echo "  celery -A config worker -l info"
echo "  celery -A config beat -l info"
echo ""
echo "Services:"
echo "  Django:          http://localhost:8000"
echo "  LibreTranslate:  http://localhost:5001"
echo "  Postgres:        localhost:5434"
echo "  Redis:           localhost:6379"

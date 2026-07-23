#!/usr/bin/env bash
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h db -p 5432 -U "${DOC_TRANSLATOR_DB_USER:-doctranslator}" >/dev/null 2>&1; do
  sleep 2
done

echo "PostgreSQL ready. Running migrations..."
python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"

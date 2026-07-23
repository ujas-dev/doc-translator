#!/bin/bash
set -e

echo "==> Installing Python dependencies..."
pip install --no-cache-dir -r /workspace/requirements.txt

echo "==> Running database migrations..."
cd /workspace
python manage.py migrate --no-input

echo "==> Collecting static files..."
python manage.py collectstatic --no-input --clear 2>/dev/null || true

echo "==> Starting Django dev server..."
exec python manage.py runserver --noreload 0.0.0.0:8000

#!/bin/bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"

mkdir -p "${BACKUP_PATH}"

echo "[$(date)] Starting backup..."

# Database backup
if command -v pg_dump &> /dev/null; then
    echo "Backing up database..."
    pg_dump "${DATABASE_URL:-postgresql://doctranslator:doctranslator@localhost:5432/doctranslator}" | gzip > "${BACKUP_PATH}/database.sql.gz"
    echo "Database backup complete."
else
    echo "pg_dump not found, skipping database backup."
fi

# Media files backup
if [ -d "/data/media" ]; then
    echo "Backing up media files..."
    tar -czf "${BACKUP_PATH}/media.tar.gz" -C /data media/
    echo "Media backup complete."
fi

# Keep only last 7 backups
echo "Cleaning old backups..."
ls -dt ${BACKUP_DIR}/*/ 2>/dev/null | tail -n +8 | xargs -r rm -rf

echo "[$(date)] Backup complete: ${BACKUP_PATH}"

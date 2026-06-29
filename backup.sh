#!/usr/bin/env bash
# Manual backup: consistent SQLite snapshot + uploaded images.
# Usage: ./backup.sh [output_dir]   (default: ./backups)
set -euo pipefail

NAME=weekly-report
OUT_DIR="${1:-./backups}"
STAMP="$(date +%Y%m%d-%H%M%S)"
DEST="${OUT_DIR}/weekly-report-${STAMP}"

mkdir -p "$DEST"

echo "Creating consistent SQLite snapshot..."
# .backup yields a consistent copy even while the app is running (WAL mode).
podman exec "$NAME" sh -c \
  "python -c \"import sqlite3,os; s=sqlite3.connect('/data/app.db'); d=sqlite3.connect('/data/_backup.db'); s.backup(d); d.close(); s.close()\""
podman cp "${NAME}:/data/_backup.db" "${DEST}/app.db"
podman exec "$NAME" rm -f /data/_backup.db

echo "Copying uploaded images..."
podman cp "${NAME}:/data/uploads" "${DEST}/uploads"

echo "Compressing..."
tar -czf "${DEST}.tar.gz" -C "$OUT_DIR" "weekly-report-${STAMP}"
rm -rf "$DEST"

echo "Backup written to ${DEST}.tar.gz"

#!/usr/bin/env bash
# Restore a backup produced by backup.sh into the weekly_data volume.
# Usage: ./restore.sh path/to/weekly-report-YYYYmmdd-HHMMSS.tar.gz
set -euo pipefail

ARCHIVE="${1:?Usage: ./restore.sh <backup.tar.gz>}"
NAME=weekly-report
VOLUME=weekly_data

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Extracting $ARCHIVE ..."
tar -xzf "$ARCHIVE" -C "$TMP"
SRC="$(find "$TMP" -maxdepth 1 -mindepth 1 -type d | head -n1)"

echo "Stopping container..."
podman stop "$NAME" >/dev/null 2>&1 || true

# Restore into the volume via a throwaway helper container that mounts it.
echo "Restoring files into volume '$VOLUME'..."
podman run --rm -v "${VOLUME}:/data" -v "${SRC}:/restore:ro" docker.io/library/busybox \
  sh -c "rm -f /data/app.db /data/app.db-wal /data/app.db-shm && \
         cp /restore/app.db /data/app.db && \
         rm -rf /data/uploads && cp -r /restore/uploads /data/uploads"

echo "Starting container..."
podman start "$NAME"
echo "Restore complete."

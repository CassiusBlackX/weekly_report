#!/usr/bin/env bash
# Build and (re)start the weekly-report container with Podman.
# Usage: ./run.sh   (reads config from .env if present)
set -euo pipefail

cd "$(dirname "$0")"

IMAGE=weekly-report:latest
NAME=weekly-report
VOLUME=weekly_data
PORT=8080

# Load .env (SECRET_KEY, ADMIN_*, TZ, COOKIE_SECURE) if it exists.
ENV_ARGS=()
if [[ -f .env ]]; then
  echo "Loading .env"
  ENV_ARGS+=(--env-file .env)
else
  echo "WARNING: no .env found; using insecure defaults. Copy .env.example to .env."
fi

echo "Building image..."
podman build -t "$IMAGE" .

echo "Ensuring volume '$VOLUME' exists..."
podman volume inspect "$VOLUME" >/dev/null 2>&1 || podman volume create "$VOLUME"

echo "Replacing container..."
podman rm -f "$NAME" >/dev/null 2>&1 || true

podman run -d \
  --name "$NAME" \
  --restart unless-stopped \
  -p 127.0.0.1:${PORT}:8080 \
  -v "${VOLUME}:/data" \
  "${ENV_ARGS[@]}" \
  "$IMAGE"

echo "Started. Local health check:"
sleep 2
curl -fsS "http://127.0.0.1:${PORT}/healthz" && echo
echo "Reverse-proxy https://yourdomain/weekly_report/ to http://127.0.0.1:${PORT}"

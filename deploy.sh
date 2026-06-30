#!/usr/bin/env bash
# One-shot packaging for transfer to the nginx server (no rebuild needed there).
# Builds the image, exports it as a gzipped tar with a sha256 checksum, and
# prints the exact scp / load / run commands.
#
# Usage:
#   ./deploy.sh                 # build, then package into ./dist/
#   ./deploy.sh --no-build      # skip build, package the current image as-is
set -euo pipefail

cd "$(dirname "$0")"

IMAGE=localhost/weekly-report:latest
OUT_DIR=dist
STAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE="${OUT_DIR}/weekly-report-${STAMP}.tar.gz"

BUILD=1
[[ "${1:-}" == "--no-build" ]] && BUILD=0

mkdir -p "$OUT_DIR"

if [[ "$BUILD" == "1" ]]; then
  echo "==> Building image (frontend + backend)..."
  podman build -t "$IMAGE" .
else
  echo "==> Skipping build (--no-build); using existing $IMAGE"
  podman image exists "$IMAGE" || { echo "ERROR: image $IMAGE not found. Run without --no-build."; exit 1; }
fi

echo "==> Exporting and compressing image..."
podman save "$IMAGE" | gzip > "$ARCHIVE"

echo "==> Writing checksum..."
# Store a bare-filename checksum so `sha256sum -c` works from inside dist/.
( cd "$OUT_DIR" && sha256sum "$(basename "$ARCHIVE")" > "$(basename "$ARCHIVE").sha256" )

SIZE="$(du -h "$ARCHIVE" | cut -f1)"
echo
echo "==================================================================="
echo "  Package ready: ${ARCHIVE}  (${SIZE})"
echo "  Checksum:      ${ARCHIVE}.sha256"
echo "==================================================================="
echo
echo "Next steps (replace user@your-server and paths):"
echo
echo "  # 1. Copy the image + checksum to the server"
echo "  scp ${ARCHIVE} ${ARCHIVE}.sha256 user@your-server:~/"
echo
echo "  # 2. (optional) copy the runtime helper files once"
echo "  scp nginx.snippet backup.sh restore.sh .env.example weekly-report.container \\"
echo "      user@your-server:~/weekly_report/"
echo
echo "  # 3. On the server: verify integrity, then load (no rebuild, no npm)"
echo "  sha256sum -c $(basename "$ARCHIVE").sha256"
echo "  podman load -i $(basename "$ARCHIVE")"
echo
echo "  # 4. First time only: create secrets and the data volume"
echo "  cd ~/weekly_report && cp .env.example .env && nano .env   # set SECRET_KEY etc."
echo "  podman volume create weekly_data"
echo
echo "  # 5. (Re)start the container from the loaded image"
echo "  podman rm -f weekly-report 2>/dev/null || true"
echo "  podman run -d --name weekly-report --restart unless-stopped \\"
echo "    -p 127.0.0.1:8080:8080 -v weekly_data:/data --env-file .env \\"
echo "    ${IMAGE}"
echo
echo "  # 6. Verify, then reload nginx"
echo "  curl -fsS http://127.0.0.1:8080/healthz"
echo "  sudo nginx -t && sudo systemctl reload nginx"
echo
echo "Note: the weekly_data volume persists across updates, so step 4 is"
echo "only needed the very first time. Updates = repeat steps 1,3,5."

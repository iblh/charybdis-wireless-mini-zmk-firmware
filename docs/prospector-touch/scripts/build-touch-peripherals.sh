#!/usr/bin/env bash
# Compile only the left and right BLE peripherals using the existing checkout.
# Run build-touch-only.sh first so the local module mirror is up to date.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source "$HERE/scripts/workspace.sh"
WORKSPACE="${1:-$(prospector_workspace "$HERE")}"
FW="$WORKSPACE/firmware"
DOCKER_DEFAULT_PLATFORM="${DOCKER_DEFAULT_PLATFORM:-linux/amd64}" \
docker compose -f "$FW/local-build/docker-compose.yml" run --rm \
  -v "$HERE/scripts/build-touch-peripherals-container.sh:/workspaces/build-touch-peripherals-container.sh:ro" \
  -v "$HERE/scripts/verify-dongle-uf2.py:/workspaces/verify-dongle-uf2.py:ro" \
  --entrypoint bash builder /workspaces/build-touch-peripherals-container.sh \
  2>&1 | tee "$FW/build/prospector-peripheral-build.log"

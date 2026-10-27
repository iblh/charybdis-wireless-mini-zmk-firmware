#!/usr/bin/env bash
# One right BLE peripheral target with USB CDC logs. No sensor wiring/timing changes.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source "$HERE/scripts/workspace.sh"
WORKSPACE="${1:-$(prospector_workspace "$HERE")}" 
FW="$WORKSPACE/firmware"
mkdir -p "$FW/build/reports"
DOCKER_DEFAULT_PLATFORM="${DOCKER_DEFAULT_PLATFORM:-linux/amd64}" \
docker compose -f "$FW/local-build/docker-compose.yml" run --rm \
  -v "$HERE/scripts/build-right-diagnostic-container.sh:/workspaces/build-right-diagnostic-container.sh:ro" \
  -v "$HERE/scripts/verify-dongle-uf2.py:/workspaces/verify-dongle-uf2.py:ro" \
  --entrypoint bash builder /workspaces/build-right-diagnostic-container.sh \
  2>&1 | tee "$FW/build/reports/right-trackball-diagnostic-build.log"

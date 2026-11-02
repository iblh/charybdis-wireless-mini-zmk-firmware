#!/usr/bin/env bash
# One right BLE peripheral target with USB CDC logs. Optional isolated delay probe.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source "$HERE/scripts/workspace.sh"
WORKSPACE="${1:-$(prospector_workspace "$HERE")}"
FW="$WORKSPACE/firmware"
DELAY="${PROSPECTOR_PMW_STARTUP_DELAY_MS:-0}"
case "$DELAY" in
  0) NAME=prospector-right-trackball-diagnostic ;;
  1000) NAME=prospector-right-trackball-delay1s ;;
  *) echo 'PROSPECTOR_PMW_STARTUP_DELAY_MS must be 0 or 1000' >&2; exit 1 ;;
esac
mkdir -p "$FW/build/reports"
DOCKER_DEFAULT_PLATFORM="${DOCKER_DEFAULT_PLATFORM:-linux/amd64}" \
docker compose -f "$FW/local-build/docker-compose.yml" run --rm \
  -e "PROSPECTOR_PMW_STARTUP_DELAY_MS=$DELAY" \
  -v "$HERE/scripts/build-right-diagnostic-container.sh:/workspaces/build-right-diagnostic-container.sh:ro" \
  -v "$HERE/scripts/verify-dongle-uf2.py:/workspaces/verify-dongle-uf2.py:ro" \
  --entrypoint bash builder /workspaces/build-right-diagnostic-container.sh \
  2>&1 | tee "$FW/build/reports/$NAME-build.log"

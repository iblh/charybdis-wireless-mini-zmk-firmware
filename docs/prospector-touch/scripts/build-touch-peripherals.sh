#!/usr/bin/env bash
# Compile BLE peripherals using the existing checkout and read-only sibling module.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source "$HERE/scripts/workspace.sh"
WORKSPACE="${1:-$(prospector_workspace "$HERE")}"
FW="$WORKSPACE/firmware"
SIDE="${PROSPECTOR_PERIPHERAL_SIDE:-both}"
case "$SIDE" in left|right|both) ;; *) echo 'Side must be left, right or both' >&2; exit 2 ;; esac
mkdir -p "$FW/build"
DOCKER_DEFAULT_PLATFORM="${DOCKER_DEFAULT_PLATFORM:-linux/amd64}" \
docker compose -f "$FW/local-build/docker-compose.yml" run --rm \
  -e "PROSPECTOR_PERIPHERAL_SIDE=$SIDE" \
  -v "$WORKSPACE/module:/workspaces/prospector-local-module:ro" \
  -v "$HERE/scripts/build-touch-peripherals-container.sh:/workspaces/build-touch-peripherals-container.sh:ro" \
  -v "$HERE/scripts/verify-dongle-uf2.py:/workspaces/verify-dongle-uf2.py:ro" \
  --entrypoint bash builder /workspaces/build-touch-peripherals-container.sh \
  2>&1 | tee "$FW/build/prospector-peripheral-$SIDE-build.log"

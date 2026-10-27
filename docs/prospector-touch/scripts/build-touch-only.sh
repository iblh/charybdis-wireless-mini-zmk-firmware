#!/usr/bin/env bash
# Usage: bash prospector-pro-handoff/scripts/build-touch-only.sh [workspace_root]
# Docker single-target build; prefers working files from ../firmware and ../module.
# Tested with the local Docker/West single-target build on 2026-10-23.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source "$HERE/scripts/workspace.sh"
WORKSPACE="${1:-$(prospector_workspace "$HERE")}"
WORKSPACE="$(cd "$WORKSPACE" && pwd)"
FW="$WORKSPACE/firmware"
MODULE="$WORKSPACE/module"
if [ ! -f "$FW/local-build/docker-compose.yml" ]; then
  echo "Missing original compose file: $FW/local-build/docker-compose.yml" >&2; exit 1
fi
if [ ! -f "$MODULE/boards/shields/prospector_adapter/src/touch_settings.c" ]; then
  echo "Missing local Prospector module at $MODULE" >&2; exit 1
fi
if ! command -v docker >/dev/null; then echo 'Install and start Docker Desktop first.' >&2; exit 1; fi
mkdir -p "$FW/build/prospector-touch"
echo 'Using local module checkout; West update is controlled by SKIP_WEST_UPDATE.'
echo "This builds ONLY nice_nano//zmk + charybdis_dongle prospector_adapter + ${PROSPECTOR_KEYMAP:-qwerty}."
echo "West update: $([ "${SKIP_WEST_UPDATE:-false}" = true ] && echo skipped || echo enabled)"
# The original project container is designed for x86_64/Linux; force Linux amd64 for consistency.
# On Apple Silicon this may use emulation, and can be slow.
DOCKER_DEFAULT_PLATFORM="${DOCKER_DEFAULT_PLATFORM:-linux/amd64}" \
docker compose -f "$FW/local-build/docker-compose.yml" run --rm \
    -e PROSPECTOR_KEYMAP="${PROSPECTOR_KEYMAP:-qwerty}" \
    -v "$MODULE:/workspaces/prospector-local-module:ro" \
    -v "$HERE/scripts/build-touch-only-container.sh:/workspaces/build-touch-only-container.sh:ro" \
    -v "$HERE/scripts/verify-dongle-uf2.py:/workspaces/verify-dongle-uf2.py:ro" \
    --entrypoint bash builder /workspaces/build-touch-only-container.sh \
    2>&1 | tee "$FW/build/prospector-touch-last-build.log"

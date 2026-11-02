#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source "$HERE/scripts/workspace.sh"
WORKSPACE="${1:-$(prospector_workspace "$HERE")}"
FW="$WORKSPACE/firmware"
INTERVAL="${PROSPECTOR_POINT_INTERVAL_MS:-12}"
ANGLE="${PROSPECTOR_POINT_ANGLE_DEG:-15}"
CPI="${PROSPECTOR_POINT_CPI:-800}"
case "$CPI" in 800|1600) ;; *) echo 'CPI must be 800 or 1600' >&2; exit 1 ;; esac
case "$INTERVAL" in 8|12) ;; *) echo 'Interval must be 8 or 12ms' >&2; exit 1 ;; esac
if [[ ! "$ANGLE" =~ ^-?[0-9]{1,3}$ ]]; then echo 'Invalid angle' >&2; exit 1; fi
NAME="prospector-right-profile-${INTERVAL}ms-angle${ANGLE}"
if [ "$CPI" != 800 ]; then NAME="$NAME-cpi$CPI"; fi
mkdir -p "$FW/build/reports"
DOCKER_DEFAULT_PLATFORM="${DOCKER_DEFAULT_PLATFORM:-linux/amd64}" \
docker compose -f "$FW/local-build/docker-compose.yml" run --rm \
  -e "PROSPECTOR_POINT_INTERVAL_MS=$INTERVAL" -e "PROSPECTOR_POINT_ANGLE_DEG=$ANGLE" \
  -e "PROSPECTOR_POINT_CPI=$CPI" \
  --entrypoint bash builder \
  /workspaces/zmk/docs/prospector-touch/scripts/build-right-profile-container.sh \
  2>&1 | tee "$FW/build/reports/$NAME-build.log"

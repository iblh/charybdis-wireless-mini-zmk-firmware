#!/usr/bin/env bash
# TARGET=dongle (QUEUE=5|64), or TARGET=right (ANGLE=15|40).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source "$HERE/scripts/workspace.sh"
WORKSPACE="${1:-$(prospector_workspace "$HERE")}"
FW="$WORKSPACE/firmware"
TARGET="${PROSPECTOR_PIPE_TARGET:-dongle}"
QUEUE="${PROSPECTOR_PIPE_QUEUE:-5}"
ANGLE="${PROSPECTOR_POINT_ANGLE_DEG:-15}"
RIGHT_ONLY="${PROSPECTOR_RIGHT_ONLY_MOUSE:-false}"
CADENCE="${PROSPECTOR_PIPE_CADENCE:-false}"
CPI="${PROSPECTOR_POINT_CPI:-800}"
BTTRACE="${PROSPECTOR_BT_TRACE:-false}"
ATT_TX="${PROSPECTOR_ATT_TX_COUNT:-3}"
RADIO_AB="${PROSPECTOR_RADIO_AB:-false}"
case "$RADIO_AB:$TARGET:$QUEUE:$CPI:$ANGLE:$CADENCE:$BTTRACE:$ATT_TX:$RIGHT_ONLY" in
  false:*) ;;
  true:dongle:64:800:15:true:false:3:false|true:right:5:800:15:true:true:3:false) ;;
  *) echo 'Radio AB requires cadence, right ATT3 trace or Dongle q64' >&2; exit 1 ;;
esac
case "$BTTRACE:$ATT_TX:$TARGET:$CPI:$CADENCE:$ANGLE:$QUEUE:$RIGHT_ONLY" in
  false:3:*) ;;
  true:3:right:800:true:15:5:false|true:8:right:800:true:15:5:false) ;;
  *) echo 'BT trace supports only right/800/8ms/15deg/cadence, ATT count 3 or 8' >&2; exit 1 ;;
esac
case "$TARGET:$QUEUE:$RIGHT_ONLY:$CADENCE" in dongle:64:false:true|right:5:false:true|*:*:*:false) ;; *) echo 'Unsupported cadence target' >&2; exit 1 ;; esac
case "$TARGET:$CPI" in dongle:800|right:800|right:1600) ;; *) echo 'Unsupported CPI/target' >&2; exit 1 ;; esac
case "$TARGET:$QUEUE:$RIGHT_ONLY" in dongle:64:true|*:5:false|dongle:64:false) ;; *) echo 'Right-only keymap requires Dongle q64' >&2; exit 1 ;; esac
case "$TARGET:$QUEUE:$ANGLE" in dongle:5:15|dongle:64:15|right:5:15|right:5:40) ;; *) echo 'Unsupported diagnostic combination' >&2; exit 1 ;; esac
mkdir -p "$FW/build/reports"
DOCKER_DEFAULT_PLATFORM="${DOCKER_DEFAULT_PLATFORM:-linux/amd64}" \
docker compose -f "$FW/local-build/docker-compose.yml" run --rm \
  -e "PROSPECTOR_PIPE_TARGET=$TARGET" -e "PROSPECTOR_PIPE_QUEUE=$QUEUE" \
  -e "PROSPECTOR_POINT_ANGLE_DEG=$ANGLE" \
  -e "PROSPECTOR_RIGHT_ONLY_MOUSE=$RIGHT_ONLY" \
  -e "PROSPECTOR_PIPE_CADENCE=$CADENCE" \
  -e "PROSPECTOR_POINT_CPI=$CPI" \
  -e "PROSPECTOR_BT_TRACE=$BTTRACE" -e "PROSPECTOR_ATT_TX_COUNT=$ATT_TX" \
  -e "PROSPECTOR_RADIO_AB=$RADIO_AB" \
  -v "$WORKSPACE/module:/workspaces/prospector-local-module:ro" \
  --entrypoint bash builder /workspaces/zmk/docs/prospector-touch/scripts/build-pipeline-container.sh \
  2>&1 | tee "$FW/build/reports/pipeline-$TARGET-q$QUEUE-a$ANGLE-cpi$CPI-rightonly-$RIGHT_ONLY-cadence-$CADENCE-bttrace-$BTTRACE-att$ATT_TX-radioab-$RADIO_AB-build.log"

#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
source "$HERE/scripts/workspace.sh"
WORKSPACE="${1:-$(prospector_workspace "$HERE")}"
WORKSPACE="$(cd "$WORKSPACE" && pwd)"
echo "=== Prospector local workspace report ==="
echo "Workspace: $WORKSPACE"
for item in firmware module; do
  repo="$WORKSPACE/$item"
  echo
  echo "[$item]"
  if ! git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "ERROR: not a git checkout: $repo"
    continue
  fi
  printf 'remote: '; git -C "$repo" remote get-url origin || true
  printf 'branch: '; git -C "$repo" branch --show-current || true
  printf 'sha: '; git -C "$repo" rev-parse HEAD || true
  echo 'modified/untracked files:'
  git -C "$repo" status --short
 done
 echo
 echo '[required files]'
 for f in \
   firmware/config/west.yml \
   firmware/build.yaml \
   firmware/config/dongle_prospector/dongle_prospector_touch.overlay \
   firmware/config/dongle_prospector/dongle_prospector_touch.conf \
   module/boards/shields/prospector_adapter/src/touch_settings.c \
   module/boards/shields/prospector_adapter/src/brightness.c; do
   if [ -f "$WORKSPACE/$f" ]; then echo "OK   $f"; else echo "MISSING $f"; fi
 done
 echo
 echo '[touch/driver build options]'
 if [ -f "$WORKSPACE/firmware/config/dongle_prospector/dongle_prospector_touch.conf" ]; then
    grep -E '^(CONFIG_PROSPECTOR_TOUCH_UI|CONFIG_INPUT_CST816S|CONFIG_LV_Z_POINTER_INPUT|CONFIG_LV_USE_(BUTTON|BAR|SLIDER)|CONFIG_PROSPECTOR_USE_AMBIENT_LIGHT_SENSOR|CONFIG_ZMK_IDLE_TIMEOUT)=' "$WORKSPACE/firmware/config/dongle_prospector/dongle_prospector_touch.conf" || true
 fi
 echo
 echo '[Docker installation]'
 command -v docker >/dev/null && docker --version || echo 'Docker missing/not on PATH'
 echo "NOTE: This report is read-only. Compare with SOURCE_MANIFEST.json; don't reset a diverged HEAD."

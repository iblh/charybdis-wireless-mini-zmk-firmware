#!/usr/bin/env bash
# Build only the two nice_nano-compatible Charybdis BLE peripherals.
# Use the same existing West checkout as build-touch-only.sh; no updates/resets.
set -euo pipefail
cd /workspaces/zmk
west zephyr-export
ROOT="$PWD"
STAGE="$ROOT/build/prospector-peripheral-config"
MARKER="$STAGE/.generated-by-prospector-peripheral-build"
if [ -e "$STAGE" ] && [ ! -f "$MARKER" ]; then
  echo "Refusing to replace non-generated configuration: $STAGE" >&2; exit 1
fi
if [ -e "$STAGE" ]; then rm -rf "$STAGE"; fi
mkdir -p "$STAGE"
cp -R "$ROOT/config/." "$STAGE/"
touch "$MARKER"
for f in "$ROOT"/config/charybdis/*.conf; do
  if [ -f "$f" ]; then cp "$f" "$STAGE/$(basename "$f")"; fi
done
for SIDE in left right; do
  SHIELD="charybdis_${SIDE}_dongle"
  cp "$ROOT/config/keymaps/qwerty.keymap" "$STAGE/$SHIELD.keymap"
  west build -p auto -s zmk/app -d "build/prospector-${SIDE}-peripheral" -b 'nice_nano//zmk' -- \
    "-DZMK_CONFIG=$STAGE" \
    "-DZMK_EXTRA_MODULES=$ROOT/boards;$ROOT/zmk-pmw3610-driver;$ROOT/prospector-zmk-module" \
    "-DSHIELD=$SHIELD"
  python3 /workspaces/verify-dongle-uf2.py "$ROOT/build/prospector-${SIDE}-peripheral/zephyr/zmk.uf2"
done

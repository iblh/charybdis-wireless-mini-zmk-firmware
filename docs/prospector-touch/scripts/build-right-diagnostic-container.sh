#!/usr/bin/env bash
set -euo pipefail
cd /workspaces/zmk
west zephyr-export
ROOT="$PWD"
STAGE="$ROOT/build/prospector-right-diagnostic-config"
MARKER="$STAGE/.generated-by-prospector-right-diagnostic"
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
cp "$ROOT/config/keymaps/qwerty.keymap" "$STAGE/charybdis_right_dongle.keymap"
west build -p auto -s zmk/app -d build/prospector-right-trackball-diagnostic \
  -b 'nice_nano//zmk' -S zmk-usb-logging -- \
  "-DZMK_CONFIG=$STAGE" \
  "-DZMK_EXTRA_MODULES=$ROOT/boards;$ROOT/zmk-pmw3610-driver;$ROOT/prospector-zmk-module" \
  '-DSHIELD=charybdis_right_dongle' \
  "-DEXTRA_CONF_FILE=$STAGE/diagnostics/pmw3610-usb.conf"
python3 /workspaces/verify-dongle-uf2.py "$ROOT/build/prospector-right-trackball-diagnostic/zephyr/zmk.uf2"

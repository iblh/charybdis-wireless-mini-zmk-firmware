#!/usr/bin/env bash
# Container expects original project at /workspaces/zmk, module at /workspaces/prospector-local-module.
set -euo pipefail
cd /workspaces/zmk
if [ ! -d .west ]; then west init -l config; fi
if [ "${SKIP_WEST_UPDATE:-false}" != "true" ]; then
  west update
else
  echo 'Using existing West checkouts; no remote revisions will be fetched.'
fi
west zephyr-export
if [ ! -d prospector-zmk-module ]; then
   echo 'prospector-zmk-module was not checked out by west' >&2; exit 1
fi
# Reuse checked-out user's actual local edits, without copying its .git metadata.
tar --exclude='.git' -C /workspaces/prospector-local-module -cf - . \
   | tar -C prospector-zmk-module -m -xf -
ROOT="$PWD"
STAGED_CONFIG="$ROOT/build/prospector-touch-config"
MARKER="$STAGED_CONFIG/.generated-by-prospector-touch-build"
if [ -e "$STAGED_CONFIG" ] && [ ! -f "$MARKER" ]; then
  echo "Refusing to replace non-generated config directory: $STAGED_CONFIG" >&2
  exit 1
fi
if [ -e "$STAGED_CONFIG" ]; then rm -rf "$STAGED_CONFIG"; fi
mkdir -p "$STAGED_CONFIG"
cp -R "$ROOT/config/." "$STAGED_CONFIG/"
touch "$MARKER"
# ZMK looks for shield configs and keymaps directly under ZMK_CONFIG.
for f in "$ROOT"/config/charybdis/*.conf; do
  if [ -f "$f" ]; then cp "$f" "$STAGED_CONFIG/$(basename "$f")"; fi
done
KEYMAP="${PROSPECTOR_KEYMAP:-qwerty}"
case "$KEYMAP" in qwerty|touch_modes) ;; *) echo "Unsupported keymap: $KEYMAP" >&2; exit 1 ;; esac
cp "$ROOT/config/keymaps/$KEYMAP.keymap" "$STAGED_CONFIG/charybdis_dongle.keymap"
MODE_CONF=""
if [ "$KEYMAP" = touch_modes ]; then MODE_CONF=";$STAGED_CONFIG/dongle_prospector/dongle_prospector_input_modes.conf"; fi
CONF="$STAGED_CONFIG/dongle_prospector"
LAYOUT="$STAGED_CONFIG/dongle_prospector_layouts"
PRISTINE_MODE=auto
CACHE="$ROOT/build/prospector-touch/CMakeCache.txt"
if [ -f "$CACHE" ] && ! grep -Fxq "CACHED_ZMK_CONFIG:STRING=$STAGED_CONFIG" "$CACHE"; then
  PRISTINE_MODE=always
fi
echo "West pristine mode: $PRISTINE_MODE"
west build -p "$PRISTINE_MODE" \
 -s zmk/app \
 -d build/prospector-touch \
 -b 'nice_nano//zmk' \
 -- \
 "-DZMK_CONFIG=$STAGED_CONFIG" \
 "-DZMK_EXTRA_MODULES=$ROOT/boards;$ROOT/zmk-pmw3610-driver;$ROOT/prospector-zmk-module" \
 '-DSHIELD=charybdis_dongle prospector_adapter' \
 '-DSNIPPET=studio-rpc-usb-uart' \
 "-DEXTRA_CONF_FILE=$CONF/dongle_prospector_common.conf;$LAYOUT/dongle_prospector_layout_operator.conf;$CONF/dongle_prospector_no_sensor.conf;$CONF/dongle_prospector_touch.conf$MODE_CONF" \
 "-DEXTRA_DTC_OVERLAY_FILE=$CONF/dongle_prospector_no_sensor.overlay;$CONF/dongle_prospector_touch.overlay"
UF2="$ROOT/build/prospector-touch/zephyr/zmk.uf2"
if [ -f "$UF2" ]; then
 python3 /workspaces/verify-dongle-uf2.py "$UF2"
 echo "SUCCESS UF2: $UF2"
 ls -lh "$UF2"
else
 echo "No UF2 output; inspect build log" >&2
 exit 1
fi

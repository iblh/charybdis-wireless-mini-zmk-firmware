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
# Resolve the manifest module using the user's read-only working tree, without
# overwriting the separate West checkout or discarding any local module edits.
MODULE=/workspaces/prospector-local-module
BUILD_NAME="${PROSPECTOR_BUILD_NAME:-prospector-touch}"
if [[ ! "$BUILD_NAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then echo 'Invalid build name' >&2; exit 1; fi
ROOT="$PWD"
STAGED_CONFIG="$ROOT/build/$BUILD_NAME-config"
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
case "${PROSPECTOR_LEFT_RECOVERY:-false}" in
  false) ;;
  true|v2)
    if [ "$KEYMAP" != touch_modes ]; then echo 'Recovery requires Touch modes' >&2; exit 1; fi
    MODE_CONF="$MODE_CONF;$STAGED_CONFIG/diagnostics/left-slot-recovery.conf"
    if [ "${PROSPECTOR_LEFT_RECOVERY}" = v2 ]; then
      MODE_CONF="$MODE_CONF;$STAGED_CONFIG/diagnostics/left-slot-recovery-v2.conf"
    fi ;;
  *) echo 'Recovery must be true, false or v2' >&2; exit 1 ;;
esac
case "${PROSPECTOR_STUDIO_USB:-false}" in
  false) ;;
  true)
    if [ "$KEYMAP" != touch_modes ] || [ "${PROSPECTOR_LEFT_RECOVERY:-false}" != false ]; then
      echo 'Studio USB requires normal Touch modes, without recovery' >&2; exit 1
    fi
    MODE_CONF="$MODE_CONF;$STAGED_CONFIG/diagnostics/studio-usb.conf" ;;
  *) echo 'Studio USB must be true or false' >&2; exit 1 ;;
esac
CONF="$STAGED_CONFIG/dongle_prospector"
LAYOUT="$STAGED_CONFIG/dongle_prospector_layouts"
PRISTINE_MODE=auto
CACHE="$ROOT/build/$BUILD_NAME/CMakeCache.txt"
if [ -f "$CACHE" ] && ! grep -Fxq "CACHED_ZMK_CONFIG:STRING=$STAGED_CONFIG" "$CACHE"; then
  PRISTINE_MODE=always
fi
echo "West pristine mode: $PRISTINE_MODE"
west build -p "$PRISTINE_MODE" \
 -s zmk/app \
 -d "build/$BUILD_NAME" \
 -b 'nice_nano//zmk' \
 -- \
 "-DZMK_CONFIG=$STAGED_CONFIG" \
 "-DZMK_EXTRA_MODULES=$ROOT/boards;$ROOT/zmk-pmw3610-driver;$MODULE" \
 '-DSHIELD=charybdis_dongle prospector_adapter' \
 '-DSNIPPET=studio-rpc-usb-uart' \
 "-DEXTRA_CONF_FILE=$CONF/dongle_prospector_common.conf;$LAYOUT/dongle_prospector_layout_operator.conf;$CONF/dongle_prospector_no_sensor.conf;$CONF/dongle_prospector_touch.conf$MODE_CONF" \
 "-DEXTRA_DTC_OVERLAY_FILE=$CONF/dongle_prospector_no_sensor.overlay;$CONF/dongle_prospector_touch.overlay"
UF2="$ROOT/build/$BUILD_NAME/zephyr/zmk.uf2"
if [ -f "$UF2" ]; then
 python3 /workspaces/verify-dongle-uf2.py "$UF2"
 if grep -qx 'CONFIG_PROSPECTOR_SPLIT_SCAN_POLICY=y' "$ROOT/build/$BUILD_NAME/zephyr/.config"; then
   python3 "$MODULE/tools/verify_scan_startup.py" \
     --elf "$ROOT/build/$BUILD_NAME/zephyr/zmk.elf" \
     --map "$ROOT/build/$BUILD_NAME/zephyr/zmk.map"
 fi
 echo "SUCCESS UF2: $UF2"
 ls -lh "$UF2"
else
 echo "No UF2 output; inspect build log" >&2
 exit 1
fi

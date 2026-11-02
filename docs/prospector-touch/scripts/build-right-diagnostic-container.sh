#!/usr/bin/env bash
set -euo pipefail
cd /workspaces/zmk
west zephyr-export
ROOT="$PWD"
DELAY="${PROSPECTOR_PMW_STARTUP_DELAY_MS:-0}"
case "$DELAY" in
  0) NAME=prospector-right-trackball-diagnostic ;;
  1000) NAME=prospector-right-trackball-delay1s ;;
  *) echo 'PROSPECTOR_PMW_STARTUP_DELAY_MS must be 0 or 1000' >&2; exit 1 ;;
esac
BUILD="$ROOT/build/$NAME"
STAGE="$ROOT/build/$NAME-config"
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
EXTRA_CONF="$STAGE/diagnostics/pmw3610-usb.conf"
if [ "$DELAY" = 1000 ]; then
  EXTRA_CONF="$EXTRA_CONF;$STAGE/diagnostics/pmw3610-delay1s.conf"
fi
west build -p auto -s zmk/app -d "$BUILD" \
  -b 'nice_nano//zmk' -S zmk-usb-logging -- \
  "-DZMK_CONFIG=$STAGE" \
  "-DZMK_EXTRA_MODULES=$ROOT/boards;$ROOT/zmk-pmw3610-driver;$ROOT/prospector-zmk-module" \
  '-DSHIELD=charybdis_right_dongle' \
  "-DEXTRA_CONF_FILE=$EXTRA_CONF"
grep -qx "CONFIG_PMW3610_ALT_INIT_POWER_UP_EXTRA_DELAY_MS=$DELAY" "$BUILD/zephyr/.config"
python3 /workspaces/verify-dongle-uf2.py "$BUILD/zephyr/zmk.uf2"

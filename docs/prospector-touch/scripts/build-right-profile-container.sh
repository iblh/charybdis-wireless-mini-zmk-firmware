#!/usr/bin/env bash
set -euo pipefail
cd /workspaces/zmk
west zephyr-export
ROOT="$PWD"
INTERVAL="${PROSPECTOR_POINT_INTERVAL_MS:-12}"
ANGLE="${PROSPECTOR_POINT_ANGLE_DEG:-15}"
CPI="${PROSPECTOR_POINT_CPI:-800}"
case "$CPI" in 800|1600) ;; *) echo 'CPI must be 800 or 1600' >&2; exit 1 ;; esac
case "$INTERVAL" in 8|12) ;; *) echo 'Interval must be 8 or 12ms' >&2; exit 1 ;; esac
if [[ ! "$ANGLE" =~ ^-?[0-9]{1,3}$ ]]; then echo 'Invalid angle' >&2; exit 1; fi
NAME="prospector-right-profile-${INTERVAL}ms-angle${ANGLE}"
if [ "$CPI" != 800 ]; then NAME="$NAME-cpi$CPI"; fi
STAGE="$ROOT/build/$NAME-config"
DRIVER="$ROOT/build/$NAME-driver"
MARKER="$STAGE/.generated-by-prospector-profile"
if [ -e "$STAGE" ] && [ ! -f "$MARKER" ]; then
  echo "Refusing to replace unmarked config: $STAGE" >&2; exit 1
fi
if [ -e "$STAGE" ]; then rm -rf "$STAGE"; fi
mkdir -p "$STAGE"
cp -R "$ROOT/config/." "$STAGE/"
touch "$MARKER"
for f in "$ROOT"/config/charybdis/*.conf; do
  if [ -f "$f" ]; then cp "$f" "$STAGE/$(basename "$f")"; fi
done
cp "$ROOT/config/keymaps/qwerty.keymap" "$STAGE/charybdis_right_dongle.keymap"
echo "CONFIG_PMW3610_ALT_REPORT_INTERVAL_MIN=$INTERVAL" >> "$STAGE/diagnostics/pmw3610-profile.conf"
python3 "$ROOT/local-build/trackball-profile/prepare_driver.py" \
  --source "$ROOT/zmk-pmw3610-driver" --output "$DRIVER" --angle "$ANGLE"
OVERLAY_ARGS=()
if [ "$CPI" = 1600 ]; then
  OVERLAY_ARGS=("-DEXTRA_DTC_OVERLAY_FILE=$STAGE/diagnostics/pmw3610-cpi1600.overlay")
fi
west build -p auto -s zmk/app -d "$ROOT/build/$NAME" \
  -b 'nice_nano//zmk' -S zmk-usb-logging -- \
  "-DZMK_CONFIG=$STAGE" \
  "-DZMK_EXTRA_MODULES=$ROOT/boards;$DRIVER;$ROOT/prospector-zmk-module" \
  '-DSHIELD=charybdis_right_dongle' \
  "-DEXTRA_CONF_FILE=$STAGE/diagnostics/pmw3610-profile.conf" "${OVERLAY_ARGS[@]}"
grep -qx "CONFIG_PMW3610_ALT_REPORT_INTERVAL_MIN=$INTERVAL" "$ROOT/build/$NAME/zephyr/.config"
grep -qx 'CONFIG_PMW3610_ALT_PROFILE=y' "$ROOT/build/$NAME/zephyr/.config"
python3 - "$ROOT/build/$NAME/zephyr/zephyr.dts" "$CPI" <<'PY'
from pathlib import Path
import re,sys
values=re.findall(r'\bcpi\s*=\s*<\s*(0x[0-9a-fA-F]+|\d+)\s*>',Path(sys.argv[1]).read_text())
assert len(values)==1 and int(values[0],0)==int(sys.argv[2]), values
print('Compiled DTS CPI verified:',sys.argv[2])
PY
python3 "$ROOT/docs/prospector-touch/scripts/verify-dongle-uf2.py" "$ROOT/build/$NAME/zephyr/zmk.uf2"

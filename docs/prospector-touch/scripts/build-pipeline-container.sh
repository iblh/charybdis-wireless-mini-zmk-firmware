#!/usr/bin/env bash
set -euo pipefail
cd /workspaces/zmk
west zephyr-export
ROOT="$PWD"
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
if [ "$TARGET" = dongle ]; then NAME="prospector-dongle-pipeline-q$QUEUE"; else NAME="prospector-right-pipeline-8ms-angle$ANGLE"; fi
if [ "$RIGHT_ONLY" = true ]; then NAME="$NAME-right-test"; fi
if [ "$CPI" != 800 ]; then NAME="$NAME-cpi$CPI"; fi
if [ "$CADENCE" = true ]; then NAME="$NAME-cadence"; fi
if [ "$BTTRACE" = true ]; then
  NAME="$NAME-bttrace-att$ATT_TX"
  python3 "$ROOT/local-build/trackball-profile/verify_bt_trace_link.py" --zephyr "$ROOT/zephyr"
fi
if [ "$RADIO_AB" = true ]; then NAME="$NAME-radioab"; fi
STAGE="$ROOT/build/$NAME-config"
APP="$ROOT/build/$NAME-zmk"
if [ -e "$STAGE" ] && [ ! -f "$STAGE/.generated-by-prospector-pipeline" ]; then
  echo "Refusing to replace unmarked config $STAGE" >&2; exit 1
fi
if [ -e "$STAGE" ]; then rm -rf "$STAGE"; fi
mkdir -p "$STAGE"
cp -R "$ROOT/config/." "$STAGE/"
touch "$STAGE/.generated-by-prospector-pipeline"
for f in "$ROOT"/config/charybdis/*.conf; do cp "$f" "$STAGE/$(basename "$f")"; done
# Use the working module read-only rather than modifying the West module checkout.
MODULE=/workspaces/prospector-local-module
python3 "$ROOT/local-build/trackball-profile/prepare_pipeline.py" --source "$ROOT/zmk" --output "$APP"
if [ "$TARGET" = dongle ]; then
  cp "$ROOT/config/keymaps/touch_modes.keymap" "$STAGE/charybdis_dongle.keymap"
  if [ "$RIGHT_ONLY" = true ]; then
    python3 "$ROOT/local-build/trackball-profile/prepare_right_only_keymap.py" \
      "$ROOT/config/keymaps/touch_modes.keymap" "$STAGE/charybdis_dongle.keymap"
    echo 'CONFIG_PROSPECTOR_KEYMAP_LABEL="RIGHT TEST"' >> "$STAGE/diagnostics/pipeline.conf"
  fi
  CONF="$STAGE/dongle_prospector"
  EXTRACONF="$CONF/dongle_prospector_common.conf;$STAGE/dongle_prospector_layouts/dongle_prospector_layout_operator.conf;$CONF/dongle_prospector_no_sensor.conf;$CONF/dongle_prospector_touch.conf;$CONF/dongle_prospector_input_modes.conf;$STAGE/diagnostics/pipeline.conf"
  echo "CONFIG_ZMK_SPLIT_BLE_CENTRAL_POSITION_QUEUE_SIZE=$QUEUE" >> "$STAGE/diagnostics/pipeline.conf"
  echo 'CONFIG_PROSPECTOR_RELEASE_TAG="T5-04-DIAG"' >> "$STAGE/diagnostics/pipeline.conf"
  if [ "$CADENCE" = true ]; then
    echo 'CONFIG_PROSPECTOR_PIPELINE_CADENCE=y' >> "$STAGE/diagnostics/pipeline.conf"
    echo 'CONFIG_PROSPECTOR_RELEASE_TAG="T5-05-TIMING"' >> "$STAGE/diagnostics/pipeline.conf"
    if [ "$RADIO_AB" = true ]; then
      echo 'CONFIG_PROSPECTOR_SCAN_AB=y' >> "$STAGE/diagnostics/pipeline.conf"
      echo 'CONFIG_PROSPECTOR_RELEASE_TAG="T5-08-RADIO"' >> "$STAGE/diagnostics/pipeline.conf"
    fi
  fi
  SHIELD='charybdis_dongle prospector_adapter'
  EXTRA_OVERLAY="$CONF/dongle_prospector_no_sensor.overlay;$CONF/dongle_prospector_touch.overlay"
  DRIVER="$ROOT/zmk-pmw3610-driver"
else
  cp "$ROOT/config/keymaps/qwerty.keymap" "$STAGE/charybdis_right_dongle.keymap"
  DRIVER="$ROOT/build/$NAME-driver"
  python3 "$ROOT/local-build/trackball-profile/prepare_driver.py" --source "$ROOT/zmk-pmw3610-driver" --output "$DRIVER" --angle "$ANGLE"
  echo 'CONFIG_PMW3610_ALT_REPORT_INTERVAL_MIN=8' >> "$STAGE/diagnostics/pmw3610-profile.conf"
  EXTRACONF="$STAGE/diagnostics/pmw3610-profile.conf;$STAGE/diagnostics/pipeline.conf"
  SHIELD=charybdis_right_dongle
  EXTRA_OVERLAY=''
  if [ "$CPI" = 1600 ]; then EXTRA_OVERLAY="$STAGE/diagnostics/pmw3610-cpi1600.overlay"; fi
  if [ "$CADENCE" = true ]; then
    echo 'CONFIG_PROSPECTOR_PIPELINE_CADENCE=y' >> "$STAGE/diagnostics/pipeline.conf"
    # Keep the preceding PMW-only profile's buffer sizes; avoid shrinking the
    # UART/log buffers while adding the two peripheral timing probes.
    echo 'CONFIG_LOG_BUFFER_SIZE=16384' >> "$STAGE/diagnostics/pipeline.conf"
    echo 'CONFIG_USB_CDC_ACM_RINGBUF_SIZE=8192' >> "$STAGE/diagnostics/pipeline.conf"
    if [ "$BTTRACE" = true ]; then
      echo 'CONFIG_PROSPECTOR_BLE_TX_TRACE=y' >> "$STAGE/diagnostics/pipeline.conf"
      # Both trace variants reserve the same extra stack for nested wrappers.
      echo 'CONFIG_ZMK_SPLIT_BLE_PERIPHERAL_STACK_SIZE=1536' >> "$STAGE/diagnostics/pipeline.conf"
      echo "CONFIG_BT_ATT_TX_COUNT=$ATT_TX" >> "$STAGE/diagnostics/pipeline.conf"
      if [ "$RADIO_AB" = true ]; then echo 'CONFIG_PROSPECTOR_HCI_TRACE=y' >> "$STAGE/diagnostics/pipeline.conf"; fi
    fi
  fi
fi
west build -p auto -s "$APP/app" -d "$ROOT/build/$NAME" -b 'nice_nano//zmk' -S zmk-usb-logging -- \
  "-DZMK_CONFIG=$STAGE" "-DZMK_EXTRA_MODULES=$ROOT/boards;$DRIVER;$MODULE" \
  "-DSHIELD=$SHIELD" "-DEXTRA_CONF_FILE=$EXTRACONF" "-DEXTRA_DTC_OVERLAY_FILE=$EXTRA_OVERLAY"
grep -qx 'CONFIG_PROSPECTOR_PIPELINE_PROFILE=y' "$ROOT/build/$NAME/zephyr/.config"
if [ "$TARGET" = dongle ]; then
  grep -qx "CONFIG_ZMK_SPLIT_BLE_CENTRAL_POSITION_QUEUE_SIZE=$QUEUE" "$ROOT/build/$NAME/zephyr/.config"
fi
python3 "$ROOT/docs/prospector-touch/scripts/verify-dongle-uf2.py" "$ROOT/build/$NAME/zephyr/zmk.uf2"

if [ "$BTTRACE" = true ]; then
  grep -qx 'CONFIG_PROSPECTOR_BLE_TX_TRACE=y' "$ROOT/build/$NAME/zephyr/.config"
  grep -qx "CONFIG_BT_ATT_TX_COUNT=$ATT_TX" "$ROOT/build/$NAME/zephyr/.config"
  OBJDUMP="$(sed -n 's/^CMAKE_OBJDUMP:FILEPATH=//p' "$ROOT/build/$NAME/CMakeCache.txt")"
  test -x "$OBJDUMP"
  "$OBJDUMP" -d "$ROOT/build/$NAME/zephyr/zmk.elf" > "$ROOT/build/$NAME/zephyr/bttrace-disassembly.txt"
  HCI_ARGS=()
  if [ "$RADIO_AB" = true ]; then HCI_ARGS=(--hci); fi
  python3 "$ROOT/local-build/trackball-profile/verify_bt_trace_link.py" --disassembly "$ROOT/build/$NAME/zephyr/bttrace-disassembly.txt" "${HCI_ARGS[@]}"
fi

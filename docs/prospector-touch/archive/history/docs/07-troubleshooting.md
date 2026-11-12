# 07 — Troubleshooting / 已知问题、排查原则

## Arduino DFU upload failed

Observed: `Failed to upgrade target ... write failed [Errno 6] Device not configured`. Bootloader detected when double RESET, disk `NICENANO`. Worked around by Arduino HEX→UF2 using Microsoft `uf2conv.py`, its same-directory `uf2families.json`, family `0xADA52840`, built start `0x00026000`; macOS `cp -X` solved extended-attribute issue. Later ZMK builds already produce UF2; do not use old conversion for ZMK.

## Arduino touch NACK

Observed screen `NOT FOUND Error: 2`. Underlying I2C was not ACKing at address `0x15`; user corrected `TP_SDA`/`TP_SCL` physical pins and immediately got `CONNECTED`. This was wiring, not firmware timeout or battery issue. Don't move already tested wires back to upstream nice_nano defaults.

## CI #39888780214 LVGL linking failure

Observed `touch_settings.c:64 undefined reference to lv_slider_get_value`, `lv_button_create`, `lv_slider_create`, `lv_slider_set_range`, `lv_slider_set_value`. Cause: LVGL 9 minimal config lacked Button/Bar/Slider Widgets. Fix added to last config:

```ini
CONFIG_LV_USE_BUTTON=y
CONFIG_LV_USE_BAR=y
CONFIG_LV_USE_SLIDER=y
```

Confirmed resolved by success of run #39911723815. The original archived implementation ZIP **predates** these lines, so do not re-run/copy its `.conf` into current firmware.

## Touch works by I2C but not on ZMK UI

Check `TP_IRQ -> P1.15`, `TP_RST -> P1.13`, correct I2C pin mapping, device ID 0xA7, Zephyr touch driver attach and IRQ edge, and pointer input node. An ACK to address 0x15 alone is insufficient. Check rotation/swap/flip after raw event confirmation. UI may also be obscured or LVGL indev integration incorrect.

## Backlight slider number changes but brightness stays fixed

Likely expected while `LCD_BL` remains tied to 3.3V. Device tree maps PWM channel to P0.29, but it has no effect until electrical connection changed. Before rewiring, verify Waveshare BL circuit and possible need for transistor/driver; **do not wire GPIO output and 3.3V simultaneously**. Software may also need polarity check (`nordic,invert`).

## Touch freezes while dragging brightness

The handoff baseline used `k_msleep` in a direct callback path. The current uncommitted local module moves the fade into a coalesced work item and defers Settings writes. Measure touch response and keyboard input after a confirmed candidate flash; neither is yet verified on hardware.

## `cp -X` reports `Device not configured` during UF2 upload

On 2026-10-23 the candidate UF2 upload reported this error, and the `NICENANO` volume immediately disappeared while the board rebooted. UF2 bootloaders automatically disconnect after a completed copy, which can race macOS's copy operation; this observation alone cannot prove failure or success. The candidate intentionally looked like the archived CI Operator UI. A subsequent `CURRENT.UF2` readback matched the local candidate's full 464,640-byte application payload, confirming this particular upload succeeded. For future checks, run `python3 prospector-pro-handoff/scripts/check-flashed-dongle.py` from the workspace root while `NICENANO` is mounted. It reads the device and reports whether the application region exactly matches one of the known images; it does not save the flash or print BLE data. The missing `SET` entry is a separate UI issue; the next local build moves and relabels it `LIGHT`, pending hardware validation.

## All-screen blank/USB recovery

Current `CONFIG_ZMK_IDLE_TIMEOUT=300000` + `CONFIG_ZMK_DISPLAY_BLANK_ON_IDLE=y`, blank after 5m; touch-wake not yet proven, lack of keyboard means replug may be needed. UF2 `NICENANO` can be accessed by double-tapping RST without removing connected LCD power when properly wired. Keep known good UF2/Arduino sketch accessible. Avoid settings_reset unless deliberately re-pairing.

## Local Docker full build slow / GitHub quota misunderstanding

Repo `local-build/build_setup.sh` loops every build matrix item, not one target. Use handoff single-target script for debugging. GitHub Actions successful run #39911723815 already produced downloadable UF2 artifact. Public repo standard runner minutes ordinarily free, but billing/artifact storage limits can differ; avoid unnecessary full-matrix CI while iterating.

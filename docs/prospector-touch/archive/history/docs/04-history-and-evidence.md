# 04 — Chronological Work Log / 已完成工作记录

## 1. Early hardware and Arduino (October 2026)

- Adopted Pro Micro-form-factor nRF52840 nice!nano-compatible MCU; Arduino Core was installed via `pdcook/nRFMicro-Arduino-Core`. Boards Manager package path in Arduino15 was renamed from `nRFMicro-like Boards` to `nRFMicro-like_Boards` after it was not recognized.
- ST7789 tested with Adafruit_GFX + Adafruit_ST7789. Arduino sketch generated RGB bars + "Hello!", "nRF52840", "SPI OK"; the LCD actually displayed them.
- Arduino DFU serial uploading initially failed: `write failed: [Errno 6] Device not configured`. Double-reset mounted `NICENANO` UF2 storage; `INFO_UF2.TXT` showed 2021 Bootloader 0.6.0, SoftDevice 6.1.1.
- Corrected Arduino linker to S140 6.x application start; HEX converted with Microsoft UF2 converter with family `0xADA52840` and start `0x26000`. `uf2conv.py` required `uf2families.json` alongside it. `cp -X` to mounted NICENANO solved macOS extended-attributes issue. **This address is the earlier Arduino build check, not a general guarantee about all UF2 images.**
- Wired CST816 class touch I2C, Arduino `Wire.endTransmission(0x15)`. First `NOT FOUND Error:2` (NACK) due to wrong physical SDA/SCL pins. User adjusted wiring and got green `CONNECTED`.
- Touch coordinates/IRQ were NOT proven by that test.

## 2. Product/architecture choice

- User wants more polished than stock Prospector: functional touch settings, manual brightness, theme UI, sleep/wake; no APDS9960 sensor; already 3D printed case; imminent Wireless Charybdis Mini 3x6.
- Selected `280Zo` combined Charybdis+Prospector stack (Zephyr 4.1, LVGL 9, nice_nano support) rather than developing a separate Arduino dashboard.
- Created two personal forks under `iblh`, local paths `~/Workspace/Lab/prospector-pro/firmware` and `.../module`.
- Original generated patch saved in `archive/2026-10-21-original-touch-patch`: scripts/apply_patch.py, firmware Touch overlay/conf, module `touch_settings.c`, header; applied using Python to both git clones.
- Fixed `west.yml` remote from unregistered `iblh` to a declared remote with `revision: feat/touch-no-sensor`.

## 3. Initial CI failure and fix

- Run #39888780214 failed only the new no-sensor touch QWERTY/Colemak-DH Jobs. `touch_settings.c` compiled but link failed with `undefined reference` to `lv_slider_get_value`, `lv_slider_create`, `lv_slider_set_range`, `lv_slider_set_value`, `lv_button_create`.
- Root cause: LVGL9 UI widgets compiled out by minimal build; patch code did not enable them.
- Added the following to **latest** firmware `config/dongle_prospector/dongle_prospector_touch.conf`:

```ini
CONFIG_LV_USE_BUTTON=y
CONFIG_LV_USE_BAR=y
CONFIG_LV_USE_SLIDER=y
```

- New run #39911723815 passed; user downloaded `firmware-dongle_prospector_nano_no_sensor-qwerty` and flashed `charybdis_dongle prospector_adapter-qwerty.uf2`.
- User reports screen powers on with new ZMK firmware. **This is the most recent physical milestone.** Exact on-screen details, touch buttons, brightness changes and BLE are not yet certified.

## 4. Other relevant project assets/decisions

- Charybdis Wireless Mini 3×6 first build planned; firmware includes PMW3610 trackball driver and custom split shields/keymaps. Different keyboards need different shields and Peripheral targets.
- Original Notion bilingual Build Guide existed earlier, with planned BOM/Assembly/Firmware/QC subordinate structures. This handoff does not claim to export or synchronize that Notion content; the Git repositories remain source of truth for code.

## Important integrity note

Previous assistant patch was incomplete (missing LVGL widget flags); don't blindly reapply archived patch. Its value here is forensic and historical; current branch source supersedes it.

# 05 — Code Architecture / 代码位置与改造接口

## Top-level split

```text
prospector-pro/
├── firmware/  [iblh/charybdis-wireless-mini-zmk-firmware]
│   ├── build.yaml                          # build matrix
│   ├── config/west.yml                     # ZMK, PMW3610, module revisions
│   ├── config/keymaps/qwerty.keymap        # keyboard behavior
│   ├── config/dongle_prospector/
│   │   ├── dongle_prospector_common.conf
│   │   ├── dongle_prospector_no_sensor.conf
│   │   ├── dongle_prospector_no_sensor.overlay
│   │   ├── dongle_prospector_touch.conf     # our enhanced config
│   │   └── dongle_prospector_touch.overlay  # our verified pinout override
│   ├── .github/workflows/build.yml
│   └── local-build/
├── module/ [iblh/prospector-zmk-module]
│   ├── Kconfig                             # CONFIG_PROSPECTOR_TOUCH_UI
│   ├── include/prospector/touch_settings.h
│   └── boards/shields/prospector_adapter/
│       ├── CMakeLists.txt                  # build src/touch_settings.c when enabled
│       ├── boards/nice_nano_nrf52840_zmk.overlay  # upstream default pinout; overridden
│       └── src/
│           ├── touch_settings.c            # SET, slider, swipe, Settings
│           ├── brightness.c                # existing fade, manual API, idle listener
│           ├── custom_status_screen.c      # compile-time layout selection
│           ├── display_rotate_init.c       # ROTATED_90/ROTATED_270
│           └── layouts/{classic,radii,field,operator}/status_screen.c
└── prospector-pro-handoff/ [these docs, archived patch and scripts]
```

## Existing UI patch (read actual files for implementation)

- `touch_settings.c`: registers `SETTINGS_STATIC_HANDLER_DEFINE` under `prospector_touch`, loads `brightness` if settings are loaded; `SET` button shows `settings_panel`; slider calls `prospector_brightness_set_manual()`, writes on release via `settings_save_one()`; screen swipe left/right shows/hides panel.
- `brightness.c`: exposes `prospector_brightness_set_manual`, `prospector_brightness_manual_step`, `prospector_brightness_is_auto`. Fades with `k_msleep()` inside a loop; calling this from LVGL event callback may block UI temporarily, and should be refactored to non-blocking worker with coalescing.
- `custom_status_screen.c` compiles in **only one** layout by `CONFIG_PROSPECTOR_STATUS_SCREEN_*`; `status_screen.c` for each layout calls `prospector_touch_settings_attach(screen)` when enabled.
- Zephyr `hynitron,cst816s` input emits `INPUT_ABS_X`, `INPUT_ABS_Y`, `INPUT_BTN_TOUCH`; `zephyr,lvgl-pointer-input` bridges input events to LVGL. Need verify IRQ, register/ID and coordinate orientation.
- `&pbl` behavior exists upstream for brightness keyboard shortcuts. Current no-sensor branch uses manual fixed brightness; no automatic ambient sensing.

## Architectural direction for completion

1. **Device/Input Services**: touch interrupt driver, button/gesture priority, display awake state, initial wake touch not activating underlying controls.
2. **Brightness Controller**: source of truth 1–100, `k_work_delayable` or equivalent non-blocking fades; persistence after drag complete; no GPIO driven incorrectly. Coordinate with ZMK activity and idle blanking.
3. **UI Settings**: panel states, access/close, brightness, sleep timeout, orientation, theme, diagnostics; use LVGL-safe display work queue, never call LVGL from ISR/foreign threads.
4. **Layout Registry**: runtime switch means per-layout create/destroy or activate/deactivate, event listener teardown, memory cleanup; upstream currently uses compile-time selections; do not render four layouts simultaneously blindly.
5. **Firmware Build/QA**: single-target Docker build and full CI on validated updates; pinned versions after stable milestone; physical touch/HID/peripheral test evidence.

## Memory and reliability

nRF52840: 256KB RAM. RGB565 full 240×280 frame ~134KB. LVGL buffer currently reduced to `CONFIG_LV_Z_VDB_SIZE=25` for RAM constraints. Four independent complete layout states may exceed heap or cause duplicate listeners; design memory ownership carefully. ZMK input/USB work should stay higher priority than display animations.

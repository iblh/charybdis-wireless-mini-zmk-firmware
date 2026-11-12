# AGENTS.md — Prospector Pro / Codex Project Instructions

## Scope and current truth

Read `prospector-pro-handoff/README.md` plus `docs/01...09` before making architectural changes. The working source is `./firmware` and `./module`; the handoff directory is documentation/reference only. This tracked handoff now lives at `firmware/docs/prospector-touch`; locate the shared workspace with `scripts/workspace.sh` instead of assuming one parent directory. The legacy workspace-level `prospector-pro-handoff` may be a symlink.

- Target hardware: Pro Micro-format nRF52840 nice!nano-v2-compatible board + Waveshare 1.69-inch ST7789V2 (240x280) + CST816T touchscreen (I2C `0x15`), no ambient light sensor. Existing printed enclosure, no mechanical work requested.
- User's real wiring is NOT 280Zo's default nice!nano wiring. Always inspect `firmware/config/dongle_prospector/dongle_prospector_touch.overlay` and `docs/02-hardware-pinout.md` before changing GPIO.
- Confirmed current Git branches: `feat/touch-no-sensor` in both repositories. Recorded SHAs: firmware `f4daf0be2b6f80fe41268e294e505ca79913f5cf`; module `ecbb1df8bd4972f324ae0981f378c6bf4e97bf3f`. Treat these as *handoff-time baselines*, not immutable HEADs.
- GitHub Actions #39911723815 succeeded. User flashed `charybdis_dongle prospector_adapter-qwerty.uf2`; user observed ZMK display light up. The exact GitHub artifact (dongle and keyboard sides) is preserved in `artifacts/ci-39911723815-qwerty/`; do not flash left/right UF2 to the dongle. This establishes only a display boot milestone, not working touch/BLE/brightness.
- Earlier #39888780214 failed at LVGL link due to `CONFIG_LV_USE_BUTTON`, `LV_USE_BAR`, `LV_USE_SLIDER` missing; corrected in latest `dongle_prospector_touch.conf`.

## Product requirements

- ZMK USB dongle central for Wireless Charybdis Mini 3×6; side boards are BLE peripherals once flashed and paired. Current keyboard availability/pairing NOT confirmed.
- Preserve Prospector Operator UI and useful state widgets; add a coherent polished touch UX, brightness controls, idle/sleep/wake handling, and persistent user settings. Four original visual layouts are **compile-time selected** upstream; any runtime switching must implement a layout lifecycle/registry and verify RAM usage. A feature is not "done" merely because it appears in a design document.
- No APDS9960 / no automatic ambient-light adjustment. Manual touch/keyboard brightness only. USB-powered dongle; no extra MCU or hardware unless technically unavoidable and explicitly justified.
- Existing 3D case was already printed; avoid 3D printing and assembly plans unless newly requested.
- Preserve keyboard HID reliability; UI must never block keyboard processing. Handle LVGL threading and `k_work` properly.

## Safety / build discipline

- BEFORE editing: `git -C firmware status --short`, `git -C module status --short`, inspect branches; do not reset, overwrite, or discard user's uncommitted work.
- Do not run the original archived `apply_patch.py` on already modified forks; it overwrites files and may regress LVGL fix.
- No `west flash` or bootloader writes blindly; double-reset to UF2 `NICENANO`; `cp -X` only a verified target UF2. Avoid changing BLE settings or running settings_reset without explicit reason and user approval.
- This clone has UF2 Bootloader 0.6.0: application writes stop at `0xAD000`, leaving only 552,960 bytes from ZMK's `0x26000` start. Linker FLASH capacity is larger and is NOT a flashing guarantee. Run `prospector-pro-handoff/scripts/verify-dongle-uf2.py` before delivering any UF2. Do not update the bootloader without explicit authorization.
- `LCD_BL` previous arrangement is tied to 3.3V. **Never connect BL to 3.3V and PWM simultaneously.** PWM output to P0.29 is a plan in the overlay; electrical drive needs schematic/measurement confirmation. Do not assert brightness works until hardware is confirmed.
- `TP_IRQ -> P1.15` needed for Zephyr interrupt driver, but physical connection and touch behavior must be checked; only I2C address ACK has been confirmed.
- Distinguish Build PASS, UI boots, Touch responds, BLE pairs, HID works, all features accepted.
- Prefer single-target local Docker/west build to recompiling the full 39-job matrix; preserve reproducibility (pin tested SHA once stable). Existing upstream `local-build/build_setup.sh` builds the full matrix and can be costly/sluggish on Mac.
- Use project docs and source for verifiable details; never invent result of a build or physical test. Edit source normally in `firmware/` and `module/`, not in reference snapshots. Update handoff docs when decisions or behaviors change.

## Implementation quality

- Maintain the two-repo boundary: firmware holds build matrix, hardware overlays and conf; module holds Prospector UI, controls, brightness, Kconfig and CMake.
- Keep LVGL version-appropriate API (LVGL 9 `lv_button_create`, `lv_slider_create`) and enable needed widgets.
- Fix touch gesture mapping based on actual screen orientation; avoid interfering with keyboard/trackball input reporting.
- Optimize RAM (nRF52840 256KiB RAM, 240×280×2 bytes >130 KiB for one RGB565 framebuffer). Prefer partial LVGL buffers and nonblocking fade. Do not claim four simultaneous themes run safely without measurements.
- Plan and implement persistence with Zephyr Settings in a namespace that does not overwrite ZMK BLE bonding data. Verify load/save/reboot behavior.
- For features still unimplemented, create actionable Git issues/tasks or TODOs without claiming production readiness.

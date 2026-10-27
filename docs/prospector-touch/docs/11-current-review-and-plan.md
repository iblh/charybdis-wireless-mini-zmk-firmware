# Prospector Touch Edition — 2026-10-23 code review and implementation plan

## Baseline and evidence

- `firmware`: `feat/touch-no-sensor` at `f4daf0be2b6f80fe41268e294e505ca79913f5cf`; clean before this session.
- `module`: `feat/touch-no-sensor` at `ecbb1df8bd4972f324ae0981f378c6bf4e97bf3f`; clean before this session.
- CI run `39911723815` passed. Archived dongle UF2 SHA-256 is `b5236a43ac9812124f711ba7baa1e66884f91385a0c84abd13fdd4b9cb2d48c2`.
- A local single-target build generated a UF2 with the *same* SHA-256. Linker memory report: Flash 464,216 / 811,008 bytes (57.24%); RAM 176,882 / 262,144 bytes (67.48%). The final wrapper step returned a shell parse error because its mounted script was edited while the build was running; compilation, link and UF2 conversion completed. A later required pristine rebuild removed its temporary local copy and log; the identical archived CI UF2 remains in `artifacts/ci-39911723815-qwerty/`.
- Local West revisions for that identical UF2: ZMK `4dd95d7840eb3d5a3f59bb29fbf1ab054715ef85`; Zephyr `10ba6d0cb38bc3d258775d27982f707599320085`; PMW3610 driver `f6e234367b22508b5c0a6bcc82437c64f320089b`; module `ecbb1df8bd4972f324ae0981f378c6bf4e97bf3f`.
- User observed the ZMK display light after flashing that dongle UF2. This is a visual boot observation, not evidence of touch, PWM brightness, BLE pairing, USB HID, persistence, or idle/wake behavior.

## Source inventory

This table records the handoff baseline before the local changes described below.

| Area | Present in source | Review finding |
|---|---|---|
| Hardware | Firmware Touch overlay overrides SPI, I2C, display and PWM pins; CST816S-compatible input at I2C `0x15` with IRQ P1.15 | SPI/display boot is observed. User confirms IRQ P1.15 is wired, but touch interrupt and coordinate behavior remain unmeasured. LCD_BL is still tied to 3.3V, so PWM cannot yet dim the display. Keep the overlay and pinout together. |
| UI | Four upstream layouts exist; Operator is selected in firmware config. Touch `SET`, slider and swipe panel are compiled into each layout. | Layout selection is a Kconfig/CMake choice. Runtime switching and layout cleanup do not exist. |
| Status | Operator widgets show layers, modifiers, WPM, batteries, and output/profile state | Widget event listeners keep static object pointers. Several listeners and delayed work handlers call LVGL directly instead of dispatching through ZMK's display work queue. They need thread-safe updates and explicit teardown before runtime layout switching. Values have not been checked against paired hardware. |
| Brightness | Manual setter and `&pbl` bindings; activity listener dims/brightens | Fading uses `k_msleep()` directly in the caller. Slider and keyboard/event callbacks can wait through a fade. PWM pin P0.29 is only a software plan while BL wiring remains unconfirmed. |
| Keymap | Shared keymaps bind `PBL_INC`, `PBL_DEC`, and `PBL_TOG` | In the no-sensor build, `PBL_TOG` returns `-ENOTSUP` because there is no auto mode. Review that binding when hardware keyboard testing starts; do not imply it changes brightness today. |
| Persistence | `prospector_touch/brightness` static settings handler; slider release calls `settings_save_one()` | Current ZMK `main()` calls `settings_load()` before `zmk_display_init()`, so the screen attach should see the loaded byte. The module has no settings commit hook and the initial slider value can diverge from keyboard `&pbl` changes. Save runs in LVGL callback. Reboot restore remains untested. |
| Idle/wake | ZMK idle timeout 300000 ms and display blank on idle | This build has `CONFIG_ZMK_POINTING=y`; current ZMK subscribes to input events for activity, so CST816 input may wake the display. `CONFIG_ZMK_SLEEP=y` has a 600000 ms threshold, but current ZMK skips poweroff while USB power is present. Keyboard wake and touch wake have not been measured. First-touch consumption is absent. |
| Build | Single-target Docker wrapper, full GitHub matrix | The wrapper now passes a local Docker build. Manifest follows moving `main`/feature refs, so a new local build is not automatically identical to successful CI. |

## Implementation order and gates

1. **Build baseline.** Run only `nice_nano//zmk` plus `charybdis_dongle prospector_adapter` QWERTY. Capture build log, exact West project SHAs, UF2 hash, `.config` and RAM/flash usage. Fix the wrapper if its real run fails, without changing or resetting either source repository.
2. **Make brightness nonblocking.** Use a coalescing delayable work item to apply short PWM steps. Slider, keyboard behavior, and activity event callbacks only set state and return. Preserve no-sensor behavior and the Operator screen. Confirm idle always targets 0 and active restores the requested manual value.
3. **Unify and persist the manual value.** Keep one source of truth in the brightness controller; load via Zephyr Settings under a Prospector-only namespace, apply after load, and debounce writes off the LVGL thread. Ensure `&pbl` and slider read the same value. Verify reboot restore on hardware.
4. **Validate touch hardware.** Confirm IRQ P1.15 and reset P1.13 wiring, raw coordinate corners, orientation, and tap/swipe behavior. Correct the pointer mapping only from those observations. The input path must not generate keyboard or trackball reports.
5. **Implement safe wake.** Determine whether Zephyr touch events can move ZMK from idle without breaking the display's own state handling. First touch should wake only; the next touch may operate the UI. Test 5-minute idle, repeated wake, USB replug, and keyboard activity.
6. **Polish settings and layouts.** Improve the touch panel for 240×280 rotated display. Marshal widget updates onto ZMK's display queue. Before runtime switching, give each layout and widget a create/destroy lifecycle, remove listeners and delayed work safely, and check LVGL heap, stack and RAM. Keep Operator as a fallback. Persist a theme choice only after switching survives repeated cycles.
7. **Integrated acceptance.** Build matching peripheral UF2s once keyboard hardware is available. Verify BLE pairing, two battery sources, layer/modifier/WPM values, USB HID and trackball while using touch. Run reconnect and soak tests; then pin compatible West SHAs and run final CI. Record separate build, visual, touch, PWM, persistence, BLE and HID results.

## Hardware constraints

Never drive LCD_BL from P0.29 while it is also tied to 3.3V. Verify the module's BL circuit and drive polarity before rewiring. Do not flash or reset BLE settings as part of a software build. The existing printed case and no-ambient-sensor decision remain in scope.

The user reports a roughly 3 mm black border on the right in landscape and points to an upstream product image with a similar border. Waveshare specifies a 32.634 mm horizontal active area within a 41.13 mm touch module dimension in that orientation, so a physical inactive border is plausible. The selected ST7789V device tree declares a portrait `y-offset = 20`, mapped to landscape `x_offset = 20` for 270° rotation. **Do not change this offset based on the border alone.** If actual pixels or widgets are clipped, compare a straight-on photo or an edge test pattern. The driver did have a separate deterministic bug: it reused already rotated offsets when orientation was set again; this is fixed by retaining immutable device-tree offsets in configuration. Touch swipes intermittently open the brightness panel and feel laggy. The former synchronous fade could contribute to stalls, but input orientation, gesture threshold, and SPI redraw time still need measured tests.

## First local implementation and test result

- `module` now applies PWM fades as one short step per delayable work invocation. ZMK activity, keyboard brightness, and LVGL slider callbacks update the requested target and return without sleeping.
- Touch and keyboard manual changes share the brightness controller's target. A Zephyr Settings handler keeps the existing `prospector_touch/brightness` key, applies it after `settings_load()`, and writes changed values after 1.2 seconds of quiet time from a work item. The slider refreshes from that target when opened.
- The new single-target build passed and produced `firmware/build/prospector-touch/zephyr/zmk.uf2`. Flash: 464,504 / 811,008 bytes (57.27%); RAM: 176,978 / 262,144 bytes (67.51%), changes of +288 Flash and +96 RAM from the identical-CI baseline. UF2 SHA-256: `773c2a61b2aae5409c4580679075eac30cf638113a117695d565f0b2981e20ff`.
- The local wrapper was fixed to refresh the copied module timestamps for Ninja, stage generated keymap/conf files under ignored `firmware/build/`, and use a pristine rebuild only when the ZMK config path changes. The staged-config build passed. Firmware source files remain at the recorded baseline SHA except for an added `build/` ignore rule; module code and README changes are uncommitted.
- A final incremental run of the staged-config wrapper passed after the ST7789V offset-state fix. Flash: 464,524 / 811,008 bytes (57.28%); RAM: 176,978 / 262,144 bytes (67.51%). UF2 SHA-256: `3176c737fd107463ea6e1aa53e351bd24915fce4baf048eb9cbd12b6e0c281cd`. Its log is `firmware/build/prospector-touch-last-build.log`, outside the pristine build directory; the only warning is an existing deprecated `KSCAN` symbol. The candidate dongle file is `firmware/build/prospector-touch-candidate-qwerty.uf2`. Use `SKIP_WEST_UPDATE=true bash prospector-pro-handoff/scripts/build-touch-only.sh` to repeat against the already fetched West revisions; omit the environment variable when intentionally updating dependencies.
- At this initial build stage, no new UF2 had been flashed. Subsequent readback and revised layout work are recorded below. Touch sensitivity, real PWM dimming, reboot restore, BLE pairing, and HID remain hardware acceptance items.

## 2026-10-23 hardware readback and revised touch entry

- The user flashed `prospector-touch-candidate-qwerty.uf2`. macOS printed `Device not configured`, but the bootloader volume immediately disconnected and the board rebooted. Reading `CURRENT.UF2` with `scripts/check-flashed-dongle.py` showed an **exact 464,640-byte application match** to this candidate. This establishes successful flashing, not touch/UI acceptance.
- The user reports no visible `SET` or slider. A host LVGL render with `CONFIG_PROSPECTOR_TOUCH_UI=y` showed the blue `SET` button at the top right overlapping the `SHIFT` status label. The host renderer now includes the actual `touch_settings.c` code and a brightness stub for visual checks.
- The Operator modifier row has been narrowed in touch builds, and the entry is a larger blue `LIGHT` button separated from the labels. Host rendering shows no overlap. New unflashed UF2: `firmware/build/prospector-touch-light-button-qwerty.uf2`, SHA-256 `fb65c866d1233b54885abe52a38aadf0da40c15f11bf178e13f0c2679ff29e59`. Single-target Docker build passed: Flash 464,572 / 811,008 bytes (57.28%), RAM 176,978 / 262,144 bytes (67.51%). The remaining warning is the existing deprecated `KSCAN` symbol.
- The original candidate and the archived CI UF2 remain intact for comparison and rollback. The new `LIGHT` layout, physical touch behavior, backlight, Settings restore, idle/wake, BLE and HID remain unverified on hardware.

## 2026-10-23 second readback and theme fix

- The user read back `CURRENT.UF2` after flashing the `LIGHT` candidate: it matches exactly, so the absence of the button is a runtime rendering defect rather than a failed flash.
- Firmware has all LVGL themes disabled. The host renderer previously used LVGL's default theme, which gave the button a blue background and white text that the firmware did not have. Rebuilding the host renderer with themes disabled reproduced the invisible button. Explicit control styles now make the button and panel visible in the matching host render; the settings title was also changed to uppercase because its font lacks lowercase glyphs.
- Final local single-target build passed: Flash 465,052 / 811,008 bytes (57.34%); RAM 176,978 / 262,144 bytes (67.51%). Image `firmware/build/prospector-touch-styled-light-qwerty.uf2` SHA-256 `ae7c8a465f9ba5eec073c1178fe025f07bd35b75101aa95eac54d2e1d523ae00`. This is **not yet flashed**. Visible controls and touch input must be checked on the user's board before acceptance. LCD_BL is still 3.3V, so UI slider movement cannot demonstrate electrical dimming.

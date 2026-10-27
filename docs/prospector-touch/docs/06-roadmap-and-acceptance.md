# 06 — Product Scope, Backlog, Acceptance Tests / 验收清单

The user wants a coherent final product plan, but all tests must be real; do not mark a feature implemented because a sketch or UI mockup mentioned it.

2026-10-26 文件整理：旧迭代 UF2 已清理，历史文件名仅作记录。最新三个 UF2、T4-01 和三布局回退版仍保留；日志/预览的新位置见 [整理记录](12-cleanup-2026-10-26.md)。

## 2026-10-27 更新：T5-02 显示状态修复与轨迹球诊断

用户报告双侧普通按键基本正确，切屏后 HID 仍工作但连接/电量显示过期，左右图示相反。
这些显示问题已做本地修复并回归；新的实机验收待进行。右侧 PMW3610 在电池和 USB
供电均完全不动，根因未定；另备只加日志的右侧诊断版。
详见 [操作、根因和测试记录](14-peripheral-state-and-trackball.md) 与
[候选清单](../releases/T5-02/README.md)。旧版本记录按历史状态保留。

## Latest candidate — MAC-DV / WIN-DV / GAME, T5-01 (2026-10-24)

User confirms T4-01 device page and two-step NICENANO entry passed. They now have
both keyboard halves: Pro Micro nRF52840 / nice!nano v2 compatible, not yet flashed
or paired. **No physical keyboard output, new-image boot, pairing or GAME behavior
is claimed for this candidate.**

Implemented in working source:
- Dedicated touch_modes keymap, preserving qwerty.keymap. Three complete 41-key
  bases: firmware Dvorak with Mac Cmd/Ctrl-QWERTY; firmware Dvorak with Windows
  Ctrl-QWERTY; direct QWERTY GAME without letter/thumb hold-tap or global combos.
- Typing home-row mods, NUM/NAV/SYM, common FN with F1–F12, digits 1–0, media,
  manual brightness and explicit mode requests. Mouse drag stays direct; FN plus
  left-middle/left-inner thumb accesses SCROLL/SLOW. Pointer layer references use
  new IDs 8/7. Original author terminal macros, BT_CLR combo and tap-dances are
  not imported into this dedicated keymap.
- Shared device MODE picker, real current/pending mode feedback. Requests run on
  the system queue after received raw positions are all released, a 350ms quiet
  interval and neutral keyboard/consumer/mouse-button HID reports. Requests can
  replace earlier pending requests; selecting current cancels pending selection.
  A linker wrapper observes fresh position events before hold-tap captures them;
  replays bypass it. Final ELF disassembly confirms the BLE input path reaches
  this wrapper. Upstream ZMK files are unchanged.
- Runtime CMD/OPT vs WIN/ALT and base/temporary-layer labels in all three status
  layouts. Classic selected names use FR Regular 36 to fit WIN-DV without clipping.
  Appearance switching remains independent of input mode. Default mode is MAC-DV;
  no new mode persistence or Bluetooth host profiles.
- New LVGL pool 65,536 B. A 64-bit host run with all three real layouts plus the
  shared info/mode/confirmation pages used about 54.4 KB before snapshot rendering;
  this is host evidence, not an nRF52840 heap measurement. Target static RAM is
  211,714 B (80.76%), including this pool. Hardware stress/high-water checks remain.

Local verification PASS:
- Production mode worker against deterministic platform shims: held/unresolved
  position protection, debounce, all HID report types, replacement/cancel, errors.
- Native ZMK mod-morph: 36 physical positions × 256 modifier masks × 2 OS profiles
  × both release orders, with keep-mods contract checks. This does not substitute
  for actual keyboard/hold-tap timing tests.
- Production editing shortcut C: Mac/Windows/GAME chords, matching key-up,
  duplicate/invalid inputs. Nine layers × 41 binding contracts, base/morph/HRM
  references, numeric layer IDs and GAME direct bindings checked.
- Production device service in QWERTY and mode configurations; actual LVGL input
  dispatcher/timers test mode selection, pending/active, errors, BACK, idle, and
  existing independent-contact/long-hold UF2 confirmations with mock services.
- Real-source Classic/Field/Operator previews checked; displayed connection,
  battery and version values in those previews are host fixtures.
- Local Docker/West single Dongle target PASS: FLASH **500,880 B**, static RAM
  **211,714 B**. UF2 **0x26000–0xA0500**, leaves **51,968 B** under 0xAD000.

Dongle artifact: `firmware/build/prospector-touch-input-modes.uf2`.
SHA-256: `256bd0cc2646e6db0fde1e4a9623175ce23ccc3a33b0de5217ecef862002e1db`.
Release T5-01, source fingerprint **6FF389**, build LA **10-24 23:16**.
Readback label: `input-modes candidate`; full manifest is the same basename `.json`.
Rollback remains user-confirmed `prospector-touch-device-page-qwerty.uf2`.

Two additional single-target peripheral builds PASS, sharing exact dependencies:
- `prospector-touch-left-peripheral.uf2`: FLASH 189,536 B, RAM 37,808 B,
  range 0x26000–0x54500. SHA-256
  `a08fafd75ea6732cebd80596c7761928c449d4beca0c6de9e91f320c60fc6a9f`.
- `prospector-touch-right-peripheral.uf2`: FLASH 198,084 B, RAM 38,608 B,
  range 0x26000–0x56600. SHA-256
  `a6dedb6ceacbfbb7688ee53639dd3978c364ad85e24e66214d1ff117798ef3b9`.
Both pass the conservative old-bootloader guard and are byte-identical to the
corresponding archived successful CI peripheral images. Right includes PMW3610.
These are keyboard-half files, never Dongle files; no settings_reset is included.
Neither has yet been flashed or paired by the user.

Dependencies recorded in manifests: ZMK `4dd95d7840eb3d5a3f59bb29fbf1ab054715ef85`,
Zephyr `10ba6d0cb38bc3d258775d27982f707599320085`,
PMW3610 `f6e234367b22508b5c0a6bcc82437c64f320089b`.
Source repos retain all pre-existing changes and remain uncommitted; source ID
identifies working source/config contents rather than claiming HEAD is the build.

Next user actions and all key positions: **docs/11-input-modes-guide.md**. First
validate Dongle UI, then flash each keyboard half separately, observe K1/K2 auto
pairing and test physical Dvorak, shortcut release orders, GAME, pointing and wake.
No automatic approval of physical acceptance follows from these local checks.

## Accepted device-page milestone — T4-01 (2026-10-24)

The user authorized the design in document 10. Phase 1 adds swipe-up device
information and two-step UF2 entry, keeping the existing QWERTY keymap and all
three status layouts. The device page is a shared top-layer instance, created on
first visit. It shows release T4-01, build time in America/Los_Angeles, working
source fingerprint 8EE7C5, QWERTY, actual USB readiness and BLE slot K1/K2 status.
Slots are not labeled left/right until their physical identities are verified.

FLASH opens a confirmation page on release of the first tap. A new contact must
hold HOLD 2S continuously for 2 seconds. Early release, leaving the button,
CANCEL, 15-second timeout and idle cancel confirmation. The service defers boot
entry to a worker and calls the same bootmode API used by ZMK reset. A failed
bootmode write does not reboot. No settings reset or bootloader update is called.
The activity listener closes the page and cancels pending work on idle.

Verification completed locally:
- Actual LVGL pointer/timer tests: independent contacts, short taps, early release,
  slide out/reentry, cancel, timeout, idle, exactly one request, immediate/deferred
  failure display. All reboot actions are mocked in this test.
- Actual service C compiled against host shims: deferred execution, busy request,
  cancel, idle refusal, scheduler failure, bootmode failure/no reboot, USB state,
  and connection-slot bounds. No hardware actions occur in this test.
- Device/confirmation pages rendered from actual UI C and visually checked;
  screenshot metadata and connection values are host mock data.
- Single-target Docker/West PASS: FLASH 516,528 B, static RAM 209,266 B (79.83%).
  UF2 0x26000–0xA4200 leaves 36,352 B below bootloader limit.

Accepted artifact: `firmware/build/prospector-touch-device-page-qwerty.uf2`.
SHA-256: `c08d5828ea1867596cb55b23d74ccba40b499683a0ae28246d601dc754978b73`.
Build manifest: same path with `.json`; readback label `device-page candidate`.
Rollback: retain the user-verified `prospector-touch-three-layouts-qwerty.uf2`.

The user subsequently confirmed that the device page and double-confirmed UF2
entry both passed and NICENANO mounts normally. This records those physical UI
and bootloader-entry milestones. Keyboard BLE/HID, slot identity and keyboard wake
are still unverified. T4-01 retains QWERTY; phase 2 input modes are a separate build.

## Latest iteration — three layouts, gesture-only brightness (2026-10-24)

The user confirmed the compact four-layout image works and its layout/swipe tests
passed. This confirms that image's boot and touch/navigation milestone; it does not
independently establish BLE/HID, 100 switching cycles, or setting restoration.
Keep `prospector-touch-four-layouts-compact-qwerty.uf2` as the accepted rollback image.

At the user's request, the next touch image removes Radii from the linked runtime
and cycles Classic → Field → Operator on left swipes (right reverses). LIGHT is
removed. Down swipes remain the brightness entry and CLOSE returns to the status
view. Operator restores its original modifier width 230 at `(25, 8)`; Classic and
Field keep their original geometry with the button overlay gone. Status children
are passive so the Classic roller cannot swallow navigation gestures; the brightness
slider and CLOSE remain interactive. Stable persisted layout IDs are retained,
with retired Radii ID 1 mapped to Operator. Boot still intentionally starts Operator.

Single-target local build passed: FLASH 513,788 B; static RAM 209,138 B (79.78%).
UF2 application range `0x26000–0xA3700` passes the old bootloader limit with 39,168 B
to spare. Link-map inspection confirms all three factories and no Radii listeners;
the linked binary has no LIGHT label. Operator's actual-source host render with
all modifiers active shows the restored full-width row without clipping. These are
local checks. The user subsequently confirmed that the three layouts cycle
correctly and swipe-down opens brightness on the three-layout image. Record these
two behaviors as physically passed; no new evidence was supplied for HID, reboot
persistence, long-duration stability, or wake-touch consumption.

Candidate: `firmware/build/prospector-touch-three-layouts-qwerty.uf2`.
SHA-256: `cc8b90ae7ee4e7fd0bc210d600faad71df08b57dc7887cb63800d1c47e4d7f74`.
Readback label: `EXACT MATCH: three-layout candidate`.
Remaining focused checks: slider/CLOSE and complete modifier row on this revision,
idle/wake, brightness after reboot, and keyboard state/HID once paired.

## Product requirements (prioritized by correctness/safety)

| Area | User-visible behavior | Implementation status at handoff | Acceptance evidence required |
|---|---|---|---|
| Base ZMK UI | Operator UI, layer, modifier, WPM, status, battery widgets | Builds; screen boots | Photograph actual statuses |
| Touch hardware | CST816T touch tap, press, swipe map to screen | User confirms three-layout cycling and downward brightness gesture pass | Keep monitoring corners, slider/CLOSE and wake gestures |
| Touch settings panel | Swipe down to open; CLOSE to return | User confirms down swipe opens brightness without LIGHT | Confirm slider/CLOSE after future UI changes |
| Manual brightness | Slider and optional keyboard shortcut | Software clamps to 10–100%; user confirms P0.29 wiring and real dimming | Confirm 10% floor and setting persists after reboot |
| Idle/sleep | 5-min inactivity blank; wake via keyboard | User confirms 5-minute blank; keyboard wake not yet tested | Test keyboard wake after pairing |
| Touch wake | First touch wakes with no accidental action | User confirms touch wake works; whether wake touch is consumed is not separately verified | Repeat wake and ensure wake touch does not activate a control |
| Persistent settings | Brightness survives reboot; later theme/sleep | Brightness handler loads via Settings and deferred save builds locally; reboot untested | Change, reboot, reconnect, verify saved value |
| Theme switching | Runtime Classic/Field/Operator | User confirms three-layout cycle is correct | Repeated switching, restore selected layout after reboot, HID latency |
| Connection stats | BLE peripherals left/right, USB host, batteries | Upstream widgets; physical test pending | Pair, disconnect, charge updates accurately |
| ZMK Studio | If valuable after RAM analysis | Disabled in current config | Optional only if within RAM and functional |
| Long-term stability | Reliable HID while touch UI active | Not tested | 100 BLE reconnects + long soak, no input loss |

## First physical test checklist (can be done before keyboard arrival)

### Latest candidate: 2026-10-24 compact four-layout image

The user's lazy-image readback reported 549,360 matching / 756,224 requested bytes,
with only 552,960 application bytes readable. The actual board reports UF2 Bootloader
0.6.0. Its upstream `uf2cfg.h` caps application writes at `0xAD000`, exactly
552,960 bytes after the ZMK start `0x26000`. Thus both previous four-layout images
exceeded this bootloader's writable application range. RAM/initialization changes
could not resolve incomplete installation; earlier heap-only explanations were
insufficient. Do not recommend either oversized image again.

The compact candidate retains all four layouts, creates only Operator at boot, and
creates other screens on first visit. Fonts are generated as role-specific glyph
subsets with sparse character maps and lossless RLE. 788 retained glyphs and their
character maps passed round-trip checks against the actual LVGL C decoder. Original
font source files remain intact. Default fallback font is Montserrat 12; explicit
widget fonts retain their original metrics and pixel values. Layout restore is still
temporarily disabled; booting Operator every time is intentional for this acceptance.

Single-target Docker/West build passed: FLASH 549,504 B, static RAM 218,690 B
(83.42%, including 49,152 B LVGL heap). Padded UF2 application range
`0x26000–0xAC300` leaves 3,328 B before the bootloader limit. The build wrapper now
rejects oversized or invalid application UF2 files even when linking succeeds.

Unflashed candidate: `firmware/build/prospector-touch-four-layouts-compact-qwerty.uf2`.
SHA-256: `14f88c4b7c84583d6add27829032ac9424c2ad60984cd45e0725c3fc299e726d`.
First require `EXACT MATCH: compact four-layout candidate`, then test Operator boot,
left/right cycling, down swipe brightness, LIGHT/CLOSE, all four layouts' glyphs,
brightness, idle/wake, and live keyboard updates. No hardware feature in this
candidate is accepted yet. No bootloader update was attempted.

2026-10-23 user report on the CI firmware: TP_IRQ is wired to P1.15 and LCD_BL is still tied to 3.3V. The first screen has roughly 3 mm of black border on the landscape right. The user found a similar border in an upstream product image; Waveshare's active-area/module dimensions make a physical border plausible, so this is not yet evidence of clipped pixels. Swiping occasionally shows a brightness prompt, but touch feels insensitive and laggy. This is partial evidence that some touch path reaches the UI, not confirmation of correct coordinates, reliable IRQs, slider operation, or physical dimming. A straight-on photo or edge test pattern and corner touch tests would distinguish bezel from clipping.

Later on 2026-10-23, copying the locally built candidate Dongle UF2 with `cp -X` returned `Device not configured`; the `NICENANO` volume disappeared immediately and the board rebooted. The screen still looked like the prior Operator UI, and the user did not see `SET` or a slider. UF2 bootloader auto-eject can produce a macOS copy error after a successful write, so the reboot alone was inconclusive. Both the CI and local candidate deliberately used the same Operator layout and `SET` UI; visual similarity could not identify the image.

Readback then reported `464640/464640` matching application bytes for the local candidate and a much smaller match for the archived CI artifact: the candidate **was flashed successfully**. A host LVGL render of the actual touch-enabled Operator layout showed the blue `SET` button overlapping the `SHIFT` modifier at the top right. The UI was revised to reserve that space and show a larger `LIGHT` button; the new UF2 builds locally, but its installation and screen behavior still require readback and physical validation.

Later the same day, the user reported copying `prospector-touch-light-button-qwerty.uf2` and rebooting. Their screen photo shows no `LIGHT` button. The local build contains the `LIGHT` string and touch settings symbol, and enables `CONFIG_PROSPECTOR_TOUCH_UI`. The subsequent `CURRENT.UF2` readback established which image was running. Do not claim the revised button is physically validated.

The user then read back `CURRENT.UF2` and got **EXACT MATCH: LIGHT button candidate** (`464640/464640` application bytes). The missing button was reproduced in a host LVGL render after disabling the default theme to match the actual firmware (`CONFIG_LV_USE_THEME_DEFAULT=n`). LVGL buttons had transparent backgrounds and inherited black text, so `LIGHT` was invisible on the black Operator screen. The module now assigns explicit colors, opacity, font, and pressed states to the button, settings panel, slider and close button. A host render without any theme shows the entry button and the open panel. A second visual check caught unsupported lowercase glyphs in the panel font; the label is now uppercase. A single-target Docker build passed with Flash 465,052 / 811,008 bytes (57.34%) and RAM 176,978 / 262,144 bytes (67.51%). New **unflashed** image: `firmware/build/prospector-touch-styled-light-qwerty.uf2`, SHA-256 `ae7c8a465f9ba5eec073c1178fe025f07bd35b75101aa95eac54d2e1d523ae00`. The user later confirmed the next candidate fixed touch mapping and that touch was smooth; the UI button and panel are visible.

The user reports touch coordinates are reversed in both screen axes, which exactly matches a 180° mirror of the rendered UI: a top-right hit is received at bottom-left, and the bottom-center close control must be tapped near top-center. The Zephyr LVGL pointer driver provides `invert-x` and `invert-y` before applying the configured 270° display rotation. Both flags are now enabled in `dongle_prospector_touch.overlay`. A single-target build passed with Flash 465,052 / 811,008 bytes and RAM 176,978 / 262,144 bytes. The mapping candidate is **unflashed**: `firmware/build/prospector-touch-touchmap-qwerty.uf2`, SHA-256 `14f9c4cd59bd80b733c95b5d6d63f16d8e7c300ee12978e8a198e2c7916412eb`. Touch mapping and slider direction require hardware confirmation.

The user confirmed the touch mapping candidate fixed touch coordinates, with smooth taps and no other observed touch issues. They also verified the five-minute idle blank and touch wake. On the UI polish candidate, home swipes no longer open brightness, LIGHT and CLOSE respond, and P0.29 PWM produces real backlight dimming. The touch slider and brightness controller clamp to 10–100%; the user has not yet confirmed the 10% floor or brightness persistence after reboot. Build passed: Flash 464,940 / 811,008 bytes (57.33%), RAM 176,978 / 262,144 bytes (67.51%). UF2: `firmware/build/prospector-touch-ui-polish-qwerty.uf2`, SHA-256 `0408e78cf0fbe4d17c9712c2bb26b396d83727344637f30709ad2b06abfe5c43`.

2026-10-24 four-layout candidate: Touch builds now compile the four original layouts together with namespaced widget/listener symbols. All four LVGL screens were created once before display load, with Field's 33 ms animation timer paused when hidden. Home swipe left/right was designed to cycle Classic → Radii → Field → Operator (left moves forward); down to open brightness. The layout was to be saved after 1.2 seconds under a separate Settings namespace. Local single-target Docker/West build **passed**: Flash 755,896 / 811,008 bytes (93.20%), static RAM 189,530 / 262,144 bytes (72.30%; includes only a 20,000-byte Zephyr LVGL object heap). Candidate: `firmware/build/prospector-touch-four-layouts-qwerty.uf2`, SHA-256 `edea118d7457a85700105f0c69b7fff52b57cb885fb3fdc4c64199db0033b515`. This candidate was subsequently flashed and **failed physical boot** (black screen); no runtime features were accepted.

The user flashed that four-layout candidate and reported a completely black, unresponsive screen. Reflashing `prospector-touch-ui-polish-qwerty.uf2` restored normal operation. Investigation found two concrete defects in the candidate: it tried to construct all four screens before first display load using the 20,000-byte `CONFIG_LV_Z_MEM_POOL_SIZE`, and its `lv_mem_monitor()` call was unsafe with `CONFIG_SYS_HEAP_RUNTIME_STATS=n` in this Zephyr integration. Which defect caused the black screen is not yet isolated. The new **unflashed diagnostic** starts with only Operator, creates another layout on first visit, uses a 49,152-byte Zephyr LVGL heap, and enables safe `lvgl_heap_stats()` logging after each creation. It deliberately boots Operator even if another selection was saved, so layout restoration is temporarily disabled while isolating startup. Local Docker/West build passed (Flash 756,072 / 811,008 bytes; static RAM 218,682 / 262,144 bytes; actual heap size confirmed as `0xc000` in the link map). UF2: `firmware/build/prospector-touch-layout-lazy-qwerty.uf2`, SHA-256 `8b1e6ff876ab5ed27760cd3ea3b063299ef3ea92b58908ca01296cfe81a5d210`. Operator's host LVGL renderer compiled and rendered with the current module source; its 64-bit host heap usage was 25,488 bytes, which cannot be used directly as the MCU's 32-bit usage. Hardware boot/switching remains unverified.

- [x] User confirms the corrected touch mapping, LIGHT/CLOSE interaction, and home swipe behavior.
- [x] User confirmed `TP_IRQ` is physically wired P1.15 on 2026-10-23. Interrupt operation and all power/BL wiring safety checks remain open.
- [x] User confirms LIGHT and CLOSE are tappable, with smooth coordinate mapping.
- [x] User confirms real LCD backlight dimming after moving BL to P0.29.
- [x] User confirms 5-minute blank and touch wake.
- [ ] Verify the 10% brightness floor and saved value after reboot.
- [ ] Attach serial logs if enabled, record warning/exception/reboot cycles.

## Keyboard-integrated tests (after physical keyboard arrives)

- [ ] Backup existing keyboard firmware/keymaps first; preserve standalone BT setup.
- [ ] Build matching `charybdis_left_dongle` and `charybdis_right_dongle` at same ZMK revision and qwerty keymap.
- [ ] Plan controlled BLE pairing/reset (bond deletion only if required; avoid unintended loss of BT pairing).
- [ ] Verify left/right separately, then jointly; battery labels in correct left/right order.
- [ ] Check Mac USB HID text input, all base/layer keys, modifiers and trackball movement/scroll.
- [ ] Verify active layer and battery displayed values reflect real events.
- [ ] Test disconnection and 100 reconnects without losing HID functionality.
- [ ] Test while rapidly swiping/adjusting UI; record missed input, latency, hangs.

## Done definition

`CI pass` ≠ `UF2 flashes` ≠ `LCD lights` ≠ `touch works` ≠ `keyboard fully works`. Require separate evidence for each and update this checklist, with observed value/date/commit when confirming. As of 2026-10-24, user has confirmed touch UI behavior, 5-minute blank/touch wake, and PWM dimming. Keyboard pairing/HID and persistence remain open.

2026-10-24 update: the user confirms the UI polish candidate has no unwanted swipe-to-open behavior, LIGHT/CLOSE are tappable, and LCD_BL wired to P0.29 produces real brightness changes. They also confirm five-minute screen blank and touch wake work. The software floor is 10%; the user has not yet specifically checked that minimum or brightness restore after reboot. Keyboard wake and paired keyboard status remain open.

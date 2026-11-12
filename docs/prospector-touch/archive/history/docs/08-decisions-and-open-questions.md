# 08 — Decisions, Constraints & Open Questions

## Firm decisions (do not revisit without strong technical reason)

1. nRF52840 Pro Micro / nice!nano v2-compatible MCU retained, no ESP32 or second MCU added by default.
2. Existing Waveshare 1.69" ST7789V2 + CST816 touch retained.
3. No APDS9960/ambient sensor and no light-sensing auto brightness. Manual/fixed brightness is desired.
4. Printed physical housing already done; no case/3D printing work needed.
5. Use 280Zo Charybdis firmware + Prospector module forks, not a separate Arduino standalone dashboard.
6. Two-git-repo workflow at `~/Workspace/Lab/prospector-pro/{firmware,module}`; preserve user changes; Work/Codex should operate on live clones.
7. Current runtime layouts are Classic / Field / Operator. The user confirmed three-layout cycling and swipe-down brightness entry. Upstream still uses compile-time selection.
8. Prioritize polished, stable user experience over a growing list of shaky features. Build correctness + physical QA mandatory.
9. Layout memory and configurable idle time are low priority by user choice. Next design covers swipe-up device information, double-confirmed UF2 entry, and MAC-DV / WIN-DV / GAME input modes. Hosts stay QWERTY; firmware supplies Dvorak and shortcut-QWERTY. One dongle connects through USB switching/unplugging; do not equate these input modes with BLE host profiles. See `10-touch-device-and-input-modes.md` (planned, not implemented).

## Technical uncertainties to resolve by evidence (do not assume)

- Exact Waveshare LCD board revision and PWM polarity/brightness curve; user confirms P0.29 dimming works on their assembly.
- Whether `TP_IRQ` event polarity is correct; user confirms touch coordinates and controls work smoothly after inversion.
- Exact current screen content, touch responsiveness and Settings behavior on newly flashed ZMK firmware.
- Actual board clone's pin labels: rely on verified nRF ports, not printed `D` mapping alone.
- Zephyr Settings startup ordering: whether brightness handler loads saved settings before `prospector_touch_settings_attach()` sets brightness, and whether reboot restores it.
- Whether keyboard is now complete/arrived; no BLE keypress/battery claims without physical testing.
- Whether four runtime LVGL layout variants and associated widgets fit device RAM and render smoothly; memory profiling needed.
- Whether touch wake should consume its first contact; basic touch wake is user-confirmed, accidental action needs targeted observation.
- Actual local machine Docker state/architecture (known user has a Mac; verify with `uname -m`, `docker version`).

## Tradeoffs

- No ambient-light sensor means fixed/manually tuned brightness. Auto dim by keyboard inactivity is still viable; distinguish from ambient-light auto brightness.
- User expects one coherent product spec; development can use internal milestones and tests, but deliver the set as a tested integrated build.
- ZMK Studio might require more RAM than available; current config explicitly disables it. Do not re-enable without memory/UX analysis.

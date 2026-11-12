# Prospector documentation working rules

Read README.md, USER-GUIDE.md, DEVELOPMENT.md and STATUS.md in this directory before changing architecture.
Sources are the sibling firmware and module repositories; archive/history and archive/reference are historical evidence.
Never apply old patch scripts over live code. Preserve local uncommitted changes and the two-repository boundary.

- Hardware is Pro Micro nRF52840 / nice!nano-v2-compatible plus Waveshare ST7789V2/CST816T; no ambient sensor or enclosure redesign.
- GPIO authority is firmware/config/dongle_prospector/dongle_prospector_touch.overlay; the verified touch/PWM wiring is in DEVELOPMENT.md.
- The existing bootloader accepts only application 0x26000..<0xAD000. Verify every delivered UF2 using scripts/verify-dongle-uf2.py.
- Never blindly flash, change the bootloader or globally clear bonds. Keep exact existing UF2 SHA and rollback. Left maintenance is opt-in, identity-scoped and one-time.
- Preserve HID reliability: LVGL on the display queue/timers, nonblocking work, 64KB heap with measured budget. Build PASS is distinct from hardware acceptance.
- Inspect both repositories' status/branches before edits; do not discard user changes. Prefer single-target local builds and exact dependency pins.
- Daily documentation is limited to the four canonical files. Old numbered docs are archived, not current instructions. Do not restore the removed prospector-pro-handoff alias.
- build/ contains deliverable UF2/RC only after cleanup. Ignored firmware/.local-artifacts/ contains original logs and compressed link evidence; preserve it during routine cleanup.
- KeyBeacon work is deferred by the user. No new status transport is implemented.

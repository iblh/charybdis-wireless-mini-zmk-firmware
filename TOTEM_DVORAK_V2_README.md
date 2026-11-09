# TOTEM V2 · Dvorak firmware / 刷写说明

This is a USB/BLE XIAO nRF52840 split ZMK firmware build for the 38-key TOTEM Choc V2 (vinivicici fork). It uses the original GEIGEIGEIST TOTEM split shield and a 38-key US Dvorak keymap.

## Files
- **TOTEM_Dvorak_LEFT.uf2**: the physical LEFT half, ZMK central; connect this half to a Mac over USB or BLE.
- **TOTEM_Dvorak_RIGHT.uf2**: the physical RIGHT half, ZMK peripheral; communicates with the left over BLE.
- **TOTEM_XIAO_SETTINGS_RESET.uf2**: optional pairing-settings reset image. Flash to BOTH halves ONLY when stored BLE bonds cause split pairing problems, then flash LEFT and RIGHT again.

## IMPORTANT: firmware side reversal diagnosis / 左右刷反诊断

Physical left row reported as `L R C G (silent)` and physical right as `Y P . , '` closely matches the exact **reversed halves** pattern. The old keymap source itself already contained the correct Dvorak base layer. This V2 release clarifies firmware names and adds reset support; it does NOT secretly remap scan columns to compensate for accidentally reversed firmware.

Expected physical rows (left-to-right, viewed from the top, inside to outside aligned as on keyboard):

```text
LEFT:   '  ,  .  P  Y       RIGHT: F  G  C  R  L
        A  O  E  U  I              D  H  T  N  S
   ESC  ;  Q  J  K  X              B  M  W  V  Z  /
             DEL TAB SPACE        ENTER ESC BACKSPACE
```

## Flashing procedure / 刷写步骤

1. Disconnect batteries if unsure of power/polarity. Use a USB-C DATA cable.
2. macOS input source: **U.S.** (QWERTY HID interpretation), **NOT** macOS Dvorak.
3. Unplug the physical right half. Double-tap the **onboard XIAO RESET** on physical **LEFT** so the UF2 drive (often `XIAO-SENSE`) appears. Copy **TOTEM_Dvorak_LEFT.uf2**. The disk disappears after completion.
4. Unplug physical left. Double-tap onboard XIAO RESET on physical **RIGHT**, copy **TOTEM_Dvorak_RIGHT.uf2**.
5. Test physical LEFT alone over USB. It must type; physical RIGHT alone cannot type as it is a peripheral.
6. Connect physical LEFT by USB; power physical RIGHT independently using battery or USB. Both should type through LEFT.

## If split pairing still fails / 如果配对失败

Swapping between central and peripheral roles often leaves incompatible previously stored BLE bonds.
1. Flash **TOTEM_XIAO_SETTINGS_RESET.uf2** to each physical half, ONE AT A TIME.
2. Flash **TOTEM_Dvorak_LEFT.uf2** to the physical left.
3. Flash **TOTEM_Dvorak_RIGHT.uf2** to the physical right.
4. Restart both sides together. If Mac BLE pairing was previously used, forget the old device entry and pair again.
Settings reset erases BT profiles and saved settings; it is optional if both halves already communicate.

## Missing keys check

If *every physical left key in the same column* remains silent AFTER using correct side firmware, check XIAO GPIO solder joints and PG1350 switch sockets. In the original left shield, columns use D4, D5, D10, D9, D8, so the far-right fifth column maps to D8. Only use an electrical continuity test with USB and battery power disconnected. Do not change ZMK keymap to compensate for a hardware fault.

## Build provenance

Official shield: https://github.com/GEIGEIGEIST/zmk-config-totem
Choc V2 PCB: https://github.com/vinivicici/totem_chv2
ZMK split documentation: https://zmk.dev/docs/features/split-keyboards
Settings-reset guide: https://zmk.dev/docs/troubleshooting/connection-issues

# CI 39911723815 — QWERTY no ambient sensor (verified archive from GitHub)

GitHub artifact: `firmware-dongle_prospector_nano_no_sensor-qwerty` (artifact ID 12482963870), published on 2026-10-23; downloaded from user's public GitHub Actions. Source firmware SHA `f4daf0be2b6f80fe41268e294e505ca79913f5cf`. The original artifact ZIP is saved alongside the three extracted UF2 files.

| UF2 | Intended board | Handoff evidence | SHA-256 |
|---|---|---|---|
| `charybdis_dongle prospector_adapter-qwerty.uf2` | Prospector Dongle MCU | User actually flashed it and reports LCD lit/boots | `b5236a43ac9812124f711ba7baa1e66884f91385a0c84abd13fdd4b9cb2d48c2` |
| `charybdis_left_dongle-qwerty.uf2` | Charybdis left half | Built only; physical flashing/pairing not confirmed | `a08fafd75ea6732cebd80596c7761928c449d4beca0c6de9e91f320c60fc6a9f` |
| `charybdis_right_dongle-qwerty.uf2` | Charybdis right half | Built only; physical flashing/pairing not confirmed | `a6dedb6ceacbfbb7688ee53639dd3978c364ad85e24e66214d1ff117798ef3b9` |

All three UF2 headers inspected: Family ID `0xADA52840` (nRF52840), target address `0x00026000`, flags `0x2000`, UF2 magic valid. These header checks do NOT prove behavioral safety or compatibility with hardware other than the intended builds.

**Danger:** The left/right UF2 are NOT the Prospector dongle firmware. Do not flash either into the dongle. Do not flash the dongle UF2 to keyboard halves. Existing BLE pairing can be lost if reset firmware is used later.

To flash the known visual-boot dongle version: enter board NICENANO UF2 mode via double RESET-to-GND, then (with proper wiring):

```bash
cp -X 'charybdis_dongle prospector_adapter-qwerty.uf2' /Volumes/NICENANO/
```

The user already has this working visual-boot milestone. For subsequent edits, keep this UF2 as rollback artifact. Confirm GPIO/PWM electrical safety if moving LCD_BL off 3.3V.

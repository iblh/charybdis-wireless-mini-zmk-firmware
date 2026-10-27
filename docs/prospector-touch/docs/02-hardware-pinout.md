# 02 — Hardware, Wiring & Bootloader / 硬件与接线

**非常重要：这些是真机测试使用的 GPIO，不是上游默认示意。** 在 Arduino 环境中 D 编号依赖 core 映射；在 Zephyr DTS 中使用 P0/P1 GPIO。

| Display/touch pin | nRF52840 pin | Confirmation / Purpose |
|---|---|---|
| LCD DIN | P0.22 | SPI MOSI; Arduino demo PASS |
| LCD CLK | P0.17 | SPI SCK; Arduino demo PASS |
| LCD CS | P0.24 | Chip select |
| LCD DC | P1.04 | Command/data |
| LCD RST | P1.06 | LCD reset |
| TP SDA | P1.00 | Confirmed after correcting SDA/SCL miswiring |
| TP SCL | P0.11 | Confirmed after correcting SDA/SCL miswiring |
| TP RST | P1.13 | Planned/previously wired; reset electrical/behavior unverified |
| TP IRQ | P1.15 | User confirmed physical connection on 2026-10-23; interrupt behavior still needs measured validation |
| LCD VCC | 3.3V | Power; share board GND |
| LCD GND | GND | Common return |
| LCD BL | P0.29 PWM as of 2026-10-24 | User confirms rewiring and real backlight dimming work with the UI polish candidate |
| LCD BL previous | 3.3V | Original always-on wiring; disconnected before PWM drive |

## Source-specific pin mismatch

Upstream `280Zo/prospector-zmk-module` default nice_nano overlay expects SCK P0.20, CS P0.11, DC P0.24 and RST P1.00, different from this physical board. The overlay `firmware/config/dongle_prospector/dongle_prospector_touch.overlay` overrides SPI, MIPI DBI, I2C and PWM, and adds input node. Never remove or replace that override without matching hardware changes.

## Touch controller

- Waveshare uses ST7789V2 240×280 display and CST816-class I2C touch at 7-bit address `0x15`.
- Prior Arduino `Wire.endTransmission(0x15)` returned status 0 (=ACK) only after correcting physical SDA/SCL placement. Earlier status 2 was NACK on address, **not** a bootloader/firmware issue.
- The Zephyr configuration uses `compatible = "hynitron,cst816s"`; the Zephyr 4.1 driver accepts certain CST816S/T IDs. Confirm actual ID/coordinates and IRQ behavior before treating touch as working.
- Zephyr display orientation may be landscape via `display_set_orientation(...ROTATED_270)`; pointer driver may rotate input but may still need swap/inversion after real gestures.
- User reports the rendered touch points are mirrored on both screen axes. The touch overlay now sets `invert-x` and `invert-y` on `zephyr,lvgl-pointer-input`; the new image has built, but physical confirmation is pending.

## Bootloader and flashing

**2026-10-24 correction: this board's UF2 Bootloader 0.6.0 cannot write the entire Zephyr-linked FLASH region.** Its application limit is `USER_FLASH_END=0xAD000` ([upstream 0.6.0 source](https://github.com/adafruit/Adafruit_nRF52_Bootloader/blob/0.6.0/src/usb/uf2/uf2cfg.h)). With ZMK starting at `0x26000`, payload capacity is 552,960 bytes. Both initial four-layout images exceeded it; the user's readback returned exactly 552,960 readable application bytes and no exact match. Do not flash those images again. `scripts/verify-dongle-uf2.py` now rejects images beyond this limit. Bootloader updates require explicit authorization; the compact build fits the existing bootloader.

The user's controller is a **Pro Micro nRF52840 board compatible with the nice!nano v2 pinout**, not an official nice!nano v2. It has no onboard reset button. The supplied front/back board photo labels an RST through-hole on the right edge and a rear RST test pad, plus several GND pads. Those markings are a guide; verify the assembled board before touching or soldering. To enter UF2 mode, momentarily connect RST to any confirmed GND twice while USB is connected. LCD VCC and GND should normally stay connected for this operation. If the installed case obstructs the pads, a small normally-open pushbutton or removable two-wire reset lead across RST and a spare GND can be routed through an existing opening without changing the case. Never connect RST to VCC, RAW or B+, and power off before altering wiring. Whether this particular assembly can enter the bootloader with the LCD powered remains to be checked.

Read from `NICENANO/INFO_UF2.TXT` earlier:

```text
UF2 Bootloader 0.6.0
Model: nice!nano
Board-ID: nRF52840-nicenano
SoftDevice: S140 version 6.1.1
Date: Jun 19 2021
```

Double-tap board RESET-to-GND (not VCC) to mount `/Volumes/NICENANO/`; LCD may remain properly powered/wired during reset. Copy the verified ZMK UF2:

```bash
ls /Volumes/NICENANO
cp -X '/absolute/path/charybdis_dongle prospector_adapter-qwerty.uf2' /Volumes/NICENANO/
```

`cp -X` prevents macOS extended-attribute copy errors. Volume may unmount immediately after valid UF2 upload. Never flash bootloader/SoftDevice/HEX by a generic utility without confirming memory layout. Disconnect power before changing wires. Do not disconnect only VCC/GND while keeping signal lines driven (possible backfeed).

## Current visual validation

User confirms the ZMK firmware lights the screen and reports a roughly 3 mm black border on the landscape right. The same kind of border appears in a referenced upstream product image; Waveshare's active area is smaller than the module outline, so do not treat the border alone as a display-offset fault. On 2026-10-24 the user confirmed corrected touch mapping is smooth, five-minute blank and touch wake work, and the UI polish candidate supports home swipes without opening brightness, LIGHT/CLOSE taps, and real backlight dimming after LCD_BL was rewired to P0.29. Minimum-brightness value, settings persistence, keyboard wake, and paired keyboard state still need checks.

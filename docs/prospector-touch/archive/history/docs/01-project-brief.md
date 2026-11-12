# 01 — Project Brief / 项目概况

## Vision

打造一个 **Prospector Touch Edition / Pro Micro Edition**：桌面上精致的 ZMK USB 接收器，服务即将完成的无线 Charybdis Mini 3×6；在原 Prospector 的 Layer、电池、Modifier、WPM、输出状态展示之上实现易用的触控、手动亮度、休眠、恢复和设置。优先复用 280Zo 模块，少造轮子。

## User decisions (binding)

- 屏幕使用现有 Waveshare 1.69" Touch LCD (SKU 27057 可能的型号，需实物核对)；MCU 使用现有 nice!nano 兼容 nRF52840 Pro Micro。
- **不购买环境光传感器**；所有亮度为手动或固定；不做自动光感。
- 3D 打印外壳已经完成；这里不含 CAD/BOM/机械装配步骤。
- 想要面向最终产品的一套一致方案，而非不停添加临时 Demo。工程上仍可进行小步验证，但定义完整的产品验收标准。
- 后续在本地 ChatGPT Work/Codex 实现，保持 Git 历史、可复现编译及备份。

## Known hardware/firmware status at handoff

| Item | State | Evidence |
|---|---|---|
| ST7789 SPI + Arduino demo | PASS | Hello / RGB screen appeared |
| CST816 I²C bus at 0x15 | PASS | User fixed SDA/SCL wiring; `CONNECTED` appeared |
| Arduino HEX → UF2 via bootloader | PASS | Address 0x26000 for Arduino demo, macOS cp -X succeeded |
| GitHub Zephyr / ZMK CI | PASS | Run 39911723815, same qwerty/no_sensor target |
| ZMK UF2 flashed + LCD lit | PASS (visual boot only) | User's most recent device report |
| Zephyr touch event, coordinates, SET button | UNVERIFIED | Need physical UI/IRQ test |
| PWM dimming | UNVERIFIED / hardware dependent | LCD_BL previously wired to 3.3V |
| Real keyboards + BLE/HID | NOT YET TESTED | Keyboard hardware not available/paired as of prior messages |
| Firmware persistence | UNVERIFIED | Settings code exists; load/reboot untested |
| Runtime theme switching, touch wake | NOT IMPLEMENTED | Compile-time layouts in upstream |

## Practical endpoint

A published source repo state with pinned modules, repeatable Docker+GitHub Actions builds, documented UF2, manual touch brightness, stable runtime UI controls, verified reconnect / USB HID, a concise recovery guide, and screenshots/video of physical acceptance tests. Do not treat a successful UF2 as product acceptance.

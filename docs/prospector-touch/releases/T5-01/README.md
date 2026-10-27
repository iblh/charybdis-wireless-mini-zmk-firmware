# T5-01 本地候选记录

本目录记录 2026-10-24 本地构建产物的 SHA-256、依赖版本、模拟 UI 预览与验收边界。
UF2 二进制保留在用户的 `firmware/build/`，不把本次提交当成正式固件发布。
源文件内容指纹 `6FF389` 对应清单中原始产物；后续文档整理/依赖固定后的构建标识可能不同。

- 最新 Dongle：`prospector-touch-input-modes.uf2`，MAC-DV / WIN-DV / GAME。
- 外设：`prospector-touch-left-peripheral.uf2`、`prospector-touch-right-peripheral.uf2`。
- 回退：T4-01 的 `prospector-touch-device-page-qwerty.uf2`。
- 三布局回退 SHA：`cc8b90ae7ee4e7fd0bc210d600faad71df08b57dc7887cb63800d1c47e4d7f74`。

用户已确认 T4-01 设备页和双重确认进入 NICENANO；T5-01 的真实键盘输入、
BLE 配对、GAME、快捷键及轨迹球仍待验收。预览图片的数据来自主机 mock。
正式复现方法见 [使用指南](../../docs/11-input-modes-guide.md)。

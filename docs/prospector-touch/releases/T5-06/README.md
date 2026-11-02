# T5-06：右侧 PMW/TX 帧间隔诊断

最新日志中 RX 与 USB 的 4438 个相邻间隔分布近似：各有 417 个 30–50ms 间隔，
并有大量短间隔成团。USB 无错误、中央队列无丢事件，主要不均匀在进入 Dongle 时已存在。
尚不能据此认定无线丢包、特定 BLE 参数或机械追踪就是根因。
完整数字与下一轮步骤见 [上游节奏定位](../../docs/20-upstream-cadence-investigation.md)。

新文件仅刷 **右键盘**：

`firmware/build/prospector-right-pipeline-8ms-angle15-cpi1600-cadence.uf2`

- SHA-256：`225520c13271e6a0e1fa527d7021102e437bec119b1a2ddd59806bdeeac9260f`。
- FLASH 240420B；静态 RAM 77184B。
- UF2 `0x26000–0x60C00`，旧 Bootloader 写入限额余 312320B，检查通过。
- 保持 1600 CPI / 8ms / 顺时针15°；实际 DTS 与旧 1600 CPI 版完全一致。
- 有效 Kconfig 只新增 `PROSPECTOR_PIPELINE_PROFILE=y`、`PROSPECTOR_PIPELINE_CADENCE=y`。
- 不改 BLE 配对、GPIO、按键、现有输入/service 优先级、原 log/ring buffer 配置。
- 新增 PMW 完整帧成功入队、GATT 本地成功接受 sync 帧的间隔分布，及外设队列/通知返回统计。
- 本地 Build/native/UF2 PASS；**实机待验收**，未自动刷写。

Dongle 保持当前 T5-05 cadence 文件，不要求重刷：
SHA `8a857e1d02c95104f95f7cb539725630095967db64d53758d9accba160715be6`。
原右侧 1600 CPI 回退文件保留，SHA
`c09e00c64bf2752856d1eeb676c7a5b0f9930f2d61c5b0e362a8c819161d83ab`。

复现：

```bash
PROSPECTOR_PIPE_TARGET=right PROSPECTOR_POINT_CPI=1600 PROSPECTOR_PIPE_CADENCE=true bash firmware/docs/prospector-touch/scripts/build-pipeline.sh
```

检查：实际 C 的 PMW 失败/成功 sync 计数、GATT 接受/拒绝与 sync 条件、四个阶段独立、
间隔桶与时间回绕、原旋转/采样门限，以及 pinned ZMK 插桩与原源码保护，均通过本地测试。
该候选为定位用途，增加统计和线程仍有开销，不宣称已优化流畅度。


## 800 CPI 速度回退（2026-11-01）

用户实测 1600 太快且卡顿未改善，后续以 800 为偏好基线。
新文件 **仅用于右键盘**：`firmware/build/prospector-right-pipeline-8ms-angle15-cpi800-cadence.uf2`。

- SHA-256：`08a690eb6425ea4d9a0671316917b463615284076078eef11681ee220807a2ca`。
- FLASH 240420B / RAM 77184B；UF2 `0x26000–0x60C00`，限额余 312320B，检查通过。
- 与上面 1600 T5-06 相比只改 CPI；Kconfig 相同、设备树仅 CPI、实际应用载荷差 2 字节。
- 保留 8ms / 顺时针 15° / PMW、TX 诊断；键位与 BLE 配对不变。
- 原 1600 与 Dongle 文件保留。800 版本本地构建验证通过，实机待验；不宣称修复卡顿。
- 最新四阶段日志结论见 [实测分析](../../docs/20-upstream-cadence-investigation.md)。

复现（构建目录名省略默认 800；交付副本明确包含 `cpi800`）：

```bash
PROSPECTOR_PIPE_TARGET=right PROSPECTOR_POINT_CPI=800 PROSPECTOR_PIPE_CADENCE=true bash firmware/docs/prospector-touch/scripts/build-pipeline.sh
```

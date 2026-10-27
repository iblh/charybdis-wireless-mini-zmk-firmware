# T5-02 显示状态修复与右侧轨迹球诊断

2026-10-27 本地候选，**待实机验证**。

- `prospector-touch-peripheral-sync.uf2`：Dongle。完整双槽状态快照、晚创建布局初始化、
  当前绑定的左右显示校正；模式/键位保持原定义。原始槽号仍显示为 K1/K2。
- `prospector-right-trackball-diagnostic.uf2`：仅右侧 BLE 外设。增加 USB 串口和 PMW3610
  日志，传感器引脚和初始化配置保持不变，供进一步定位完全无指针问题。

UF2 保留在本地 `firmware/build/`；本目录保存同名 JSON 校验清单。
操作与本地测试证据见 [诊断说明](../../docs/14-peripheral-state-and-trackball.md)。

本次 module：`6299108bef48df59bdb22ef85ea57199b9ced598`。
固件清单固定此提交。单目标构建、UF2 上限与回归测试通过，不代表轨迹球或新 UI 已实机通过。

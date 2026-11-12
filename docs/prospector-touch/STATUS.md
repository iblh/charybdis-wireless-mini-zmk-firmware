# 当前状态 — 2026-11-12

## 当前基线

v0.1.0-rc1冻结原二进制，不是全面验收的stable。
Dongle为T5-12-USB / SOURCE A9EA70；左侧正常外设；右侧800CPI/ATT3/8ms/顺时针15°，仍含诊断统计。
用户已刷入，现有配置无需因目录整理重刷。

| 项目 | 当前证据 |
|---|---|
| 新固件启动、左右连接 | 用户确认全部刷好、没有问题，左右均连接 |
| USB Studio / KeyPeek | 能连接并收到标准锁提示；解锁后读取全部键位仍待确认 |
| 旧版触屏、PWM、三布局、设备页确认刷机 | 已有用户实机验收 |
| T5-12完整UI/休眠/USB切换/长期回归 | 分别待验收，不从旧版结果推定 |
| r2扫描策略 | 右侧自动连接/断电重连通过，用户报告轨迹球明显改善 |
| 32位64KB LVGL与native | 本地通过；不等于完整实机验收 |
| 固定SHA重建 | 与已验收Dongle仅SOURCE/时间11字节不同，config/DTS一致，ELF和UF2检查通过 |
| 新全矩阵CI | 未运行 |
| KeyBeacon/实时桌面状态 | 用户要求暂不开发；目前无该功能 |

[RC1清单与本地重现记录](releases/v0.1.0-rc1/README.md)。锁提示的处理在[使用指南](USER-GUIDE.md#studio--keypeek查看键位)。

## 下一步

1. 保持网页连接，在DEVICE点USB EDITOR / UNLOCK，确认可读取九层键位，不编辑/重排层。
2. 覆盖双侧分别断电重连、完整快捷键、鼠标点击/滚动/拖拽、长时间输入。
3. 回归T5-12五分钟休眠/触摸唤醒、macOS/Windows USB切换与主机睡眠唤醒。
4. 将右侧方向/位移累计/8ms逻辑与诊断统计分离，单变量比较后再准备stable。
5. 暂不调整CPI/ATT/报告间隔，不加入KeyBeacon实验。

## 本轮目录整理

- 删除工作区`prospector-pro-handoff`快捷链接；真实文档仍在`firmware/docs/prospector-touch/`。
- 日常文档收敛为README、USER-GUIDE、DEVELOPMENT、STATUS；01–34原文和旧参考材料移入历史归档。
- `build/`约618MiB收敛为约3.5MiB，只留四份UF2和RC包；固件/RC包SHA不变。
- 删除17个剩余生成目录，逻辑大小442452718B；先保存7797份必要证据，压缩49445090B。
  本轮净回收约374.8MiB；原始日志184份保留并核对，开发依赖保留。
- 旧归档/原始日志统一到`.local-artifacts/`，这些是本地证据而非日常阅读文档。
- 本轮不修改固件运行时代码，不刷写硬件、不改配对；原有`firmwares/.gitignore`的本地删除保持原状。

[本轮机器收据](archive/history/cleanup-2026-11-12-final.json) ·
[原交接历史](archive/history/README.md) ·
[KeyBeacon研究归档，仅供以后参考](archive/history/docs/33-keybeacon-assessment.md)。

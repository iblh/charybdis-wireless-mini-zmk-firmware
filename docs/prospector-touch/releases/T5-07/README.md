# T5-07：右侧 ATT 缓冲等待与本地完成诊断

**2026-11-01 实机日志更新：** 用户已完成 ATT3/ATT8 两版采集，反馈区别不明显、ATT8 可能稍好。
两轮无记录到的 SPI/队列/USB 错误；ATT8 仅减少上游等待，RX/USB 节奏未改善。
**不将 ATT8 作为默认修复**；候选保留。DONE 的本机含义需按 buffer/controller 交付解释。
[数据与后续定位](../../docs/22-att3-att8-results.md)。此前“待验收”指发布时状态，长期可靠性仍未验收。

目标：将之前最长 32–36ms 的通知 API 调用拆成分配、提交及提交后的本地完成；
保留 800 CPI / 8ms / 顺时针 15°。**只刷右键盘**，Dongle 和左侧不更新。
两个 UF2 是诊断/对照候选，不宣称卡顿修复，实机均待验收；未自动刷入。

| 变体 | firmware/build 下的文件 | 静态 RAM | SHA-256 |
|---|---|---:|---|
| ATT3 | `prospector-right-bttrace-cpi800-att3.uf2` | 79072B | `ace793ec2b4b33ad20fea8694a6b51a6718290838487c80c4763a956f296df1a` |
| ATT8 | `prospector-right-bttrace-cpi800-att8.uf2` | 79912B | `8db1a95d3de9daa5e95f3d2d65e9559cce4b2fe82b84abeea4b993b4bf88140f` |

两版 FLASH 均 242164B；UF2 均 `0x26000–0x61200`，Bootloader 0.6.0 限额余 310784B。
实际设备树完全相同，和此前 800 CPI 版相同；实际 PMW 驱动/旋转源码均相同。
ATT3/ATT8 的有效 Kconfig **仅差 CONFIG_BT_ATT_TX_COUNT=3/8**。ACL/connection TX 数仍为 3。
两版共有的诊断开销：回调和时长直方图、静态 32 槽，外设 service 栈由 756 增至 1536B。
相对此前 T5-06 的有效 Kconfig 只新增 TRACE=y 与该栈大小调整（ATT3）；原始 UF2 保留。

已通过本地检查：

- 两目标 Docker/west Build PASS，未跑全矩阵。
- 真实 trace C 的回调竞态、无订阅、分配/提交错误、跨线程隔离、槽耗尽继续发送、
  报表跨窗口存活、时长桶边界与计时回绕。
- 现有 pipeline、cadence、PMW/旋转 native 回归 PASS。
- 两个实际 ELF 的反汇编证明 `bt_att_chan_create_pdu` 调用 wrapped allocator，
  `gatt_notify` 调用 wrapped ATT send；原始函数仍存在。
- Zephyr/ZMK/driver checkout 保持干净，源码清单与有效配置 hash 见旁边 JSON。
- 交付副本 UF2 序列、向量、旧 Bootloader 写入范围检查 PASS。

Dongle 保持 `prospector-dongle-pipeline-q64-cadence.uf2`，SHA
`8a857e1d02c95104f95f7cb539725630095967db64d53758d9accba160715be6`。
右侧原 800 回退 `prospector-right-pipeline-8ms-angle15-cpi800-cadence.uf2`，SHA
`08a690eb6425ea4d9a0671316917b463615284076078eef11681ee220807a2ca`。

**完整刷写、双端 150 秒采集命令、动作表、判断与其他方案研究：**
[21 — 缓冲等待与完成诊断](../../docs/21-ble-buffer-and-completion.md)。

# T5-08：HCI 完成与扫描自动 ABBA

**实机诊断已验证（2026-11-01）：** 新ZIP确认四段切换及结束恢复成功、HCI计数无匹配异常。
后台扫描关闭使周期性30–50ms接收空档显著减少，重新开启复现；用户确认有改善仍有颗粒感。
诊断候选会恢复原扫描，尚非扫描策略修复版。见 [完整实测结论](../../docs/24-scan-ab-results-and-fix.md)。
下面“待验收”保留发布时历史状态；长期可靠性和正式修复仍待验收。

本地 Build/native/实际链接/UF2 检查通过；实机未验收，未自动刷写，不宣称卡顿改善。
保持 800 CPI / ATT3 / 8ms / 顺时针 15°。用户本轮各刷一次右侧和 Dongle，
一条命令运行 80 秒 ON/OFF/OFF/ON、约 95 秒双端采集，自动摘要并打包一个 ZIP。

| 目标 | firmware/build 下的文件 | FLASH | 静态 RAM | UF2 应用结束 | 旧 Bootloader 余量 |
|---|---|---:|---:|---|---:|
| 右侧 | `prospector-right-hci-cpi800-att3.uf2` | 243420B | 79536B | 0x61700 | 309504B |
| Dongle | `prospector-dongle-scan-ab.uf2` | 543164B | 222578B | 0xAAA00 | 9728B |

右侧 SHA-256：`c471b19320f3ef6f4f5a26327a722d461a234f319e9ae7e6f6285b43f6082246`。

Dongle SHA-256：`138184a32f64c91244749ec5cf417504d9e94becc374c4d186d7eb805e95672b`。

两目标的设备树与各自 T5-07 ATT3 / T5-05 Dongle 相同。有效 Kconfig 的变化：
右侧只新增 HCI_TRACE=y；Dongle 只新增 SCAN_AB=y 和 T5-08-RADIO 标识。
实际驱动、采样门限、GPIO、按键、PHY、interval/latency、ATT3 配额均保留。
阶段之间唯一行为变化为后台扫描开关；新的诊断开销在所有阶段共同存在。
原始依赖 checkout 干净，使用私有 ZMK app staging 和链接器 wrapper，未修改 West 内核。

本地证据：

- 右侧实际 ELF 验证 ATT 分配/提交与 controller ACL/Number Of Completed Packets 编码调用均经过探针。
- 真实 HCI C：批完成 FIFO、提前完成、失败、满槽不影响原包流、断连重置与序号/时间回绕。
- 真实扫描 C 与 pinned central helper：ABBA、OFF 时禁止重启扫描、结束/STOP/断连/API 错误恢复、run 校验。
- 一键采集器：PTY 命令字节、并行子采集器、nonce/完整窗口/恢复验证、保守 HCI 窗口与 ZIP，均为模拟。
- 原 pipeline、cadence、PMW profile/旋转与旧采集器回归通过。
- 两个交付副本均通过 UF2 block/向量/0xAD000 限额检查；没有自动给实机刷写或执行扫描实验。

回退文件保留：

- 右侧 `prospector-right-bttrace-cpi800-att3.uf2`，SHA
  `ace793ec2b4b33ad20fea8694a6b51a6718290838487c80c4763a956f296df1a`。
- Dongle `prospector-dongle-pipeline-q64-cadence.uf2`，SHA
  `8a857e1d02c95104f95f7cb539725630095967db64d53758d9accba160715be6`。

[刷写、一条采集命令、动作与决策标准](../../docs/23-hci-and-scan-ab.md)。
源码/工具快照、依赖 SHA、有效配置、设备树 hash 见两个 JSON 清单。

# T5-09：Dongle 连接数量扫描策略

> **已发现实机连接回归，请勿继续刷此文件。** 屏幕启动正常，但键盘无法连接；仅回退 T5-08 可恢复。
> 根因和替代候选见 [T5-09B](../../archive/history/docs/26-scan-startup-regression.md)。原文件及哈希保留用于回归校验。

只刷 **Dongle**：`firmware/build/prospector-dongle-scan-policy.uf2`。
标识 **T5-09-SCAN / SOURCE 20BD12**。
SHA-256：`5999c722c7c20be66198adbb4d5869198420cb7ddeef2adb82ee0e4794e808aa`。

右侧保留当前800 CPI / ATT3 / 8ms / 15°，未编译/刷写，文件hash保持原值。

- 0侧连接：30ms窗口/60ms间隔快速扫描。
- 1侧连接：5ms窗口/200ms间隔背景扫描，保留缺侧自动发现。
- 2侧连接：停止扫描；连接进行中也暂停，回调后重新判断。
- 失败重试约1秒，非阻塞锁，低优先级队列栈1536B；停扫描失败不会占死CONNECTING槽。
- 保留两外设槽、64项中央队列、7.5ms/latency30、键位、硬件接线、原BLE绑定。

本地普通Docker/west单目标构建PASS。FLASH 501672B，静态RAM 213442B。
UF2 `0x26000–0xA0800`，Bootloader 0.6.0限制余51200B，检查PASS。
实际构建只编译generated BLE central，原West文件hash未变；
普通模块CMake集成，未知central版本直接失败，不静默回退到未修复代码。

Native直接运行实际策略/生成连接发起代码：0/1/2侧、连接中、连接失败、停止失败、锁竞争、
重试、全部掉线时由慢转快、disable及调用期间状态变化、EALREADY恢复均通过。
历史pipeline/cadence/扫描AB native回归通过。实机表现、真实重连及双侧发现 **待验收**。
没有自动给设备刷写，也没有把低占空比的效果声明为已验证。

右侧文件未变：`prospector-right-hci-cpi800-att3.uf2`，SHA
`c471b19320f3ef6f4f5a26327a722d461a234f319e9ae7e6f6285b43f6082246`。
Dongle回退保留：`prospector-dongle-scan-ab.uf2`，SHA
`138184a32f64c91244749ec5cf417504d9e94becc374c4d186d7eb805e95672b`。

[最短验收、技术边界与普通构建复现](../../archive/history/docs/25-scan-policy-fix.md)。
该版本含两仓库未提交修改；未运行远程CI，发布前需同步模块并更新west pin。

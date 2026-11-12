# T5-09B：扫描策略启动顺序修复／当前单侧基线

只刷 **Dongle**：`firmware/build/prospector-dongle-scan-policy-r2.uf2`。
设备页 **T5-09B-SCAN / SOURCE 3C52B1**。
SHA-256：`99e0b1f4914b8b6eb4ccd257614216b065567e0cda721815bf7ab445a9df4e6c`。

修正 T5-09 中生成central提前初始化、Settings回调丢失导致无法连接的回归。
BLE/settings、central、状态观察模块明确按50/51/52初始化；新增真实ELF顺序校验。
原0/1/2侧扫描策略不变。右侧仍800 CPI / ATT3 / 8ms，不刷写、不清除绑定。

本地单目标Build、扫描策略native、启动生命周期复现/修复测试、实际ELF顺序与UF2限制检查通过。
FLASH 501672B，静态RAM 213442B，UF2末端0xA0800，Bootloader限额余51200B。
**用户已确认右侧自动连接、断电重连正常，轨迹球控制明显改善。**
双侧发现/重连、长时间稳定性和新一轮定量节奏仍待验收；未运行远程CI。

旧T5-09已标记有回归，原文件保留。回退仍用T5-08 `prospector-dongle-scan-ab.uf2`。
[根因、验证证据和最短步骤](../../archive/history/docs/26-scan-startup-regression.md)。

本轮源码整理、固定模块依赖与后续任务见 [当前基线](../../archive/history/docs/27-current-baseline-and-next-steps.md)。
原UF2不覆盖，不要求为整理源码重刷。

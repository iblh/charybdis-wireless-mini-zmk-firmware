# T5-11：保留K1右侧配对，检查并定向释放K2旧左侧

用户已明确授权：裸左侧新主控刷写后仍为K1 ON/K2 --，检查旧左侧是否占槽，并在保留右侧配对的情况下处理。
该授权覆盖本次精确定向清理，无需再次确认。未授权清除全部绑定、Bootloader修改或右侧重刷。

## 后续实机反馈与再次换板

用户已确认本次 v1 维护后 **LEFT CLEARED、K1 ON、K2 ON**；右侧保持原绑定，第一次替换的裸左侧已加入。
未验证裸板上的实际按键矩阵。2026-11-10 用户确认之后又更换了另一块左主控。
v1 完成记录会阻止重复删除，因此本文件中的旧 UF2 **不适用于第二次替换**；
第二次使用独立 v2 事务，见 [T5-12 完整步骤](31-controls-usb-studio.md)。

## 当时能确认什么

固定源码确认 `ble/peripheral_addresses/1` 即使外设离线也会占住地址槽。
新主控身份与旧左侧不同；K2 --只表示未连接，不能证明绑定地址槽为空。
本地未读取用户Dongle的真实NVS，因此不提前宣称已经找到旧记录或已修复。
维护固件在设备上读取存储，条件满足时处理，并将结果显示在设备页。

## 只刷Dongle

文件：`firmware/build/prospector-dongle-left-slot-recovery.uf2`。
设备页：**T5-11-LEFT / SOURCE A31BE3**。
SHA-256：`b0f990d98a51f9003505262cc13af96f8e5f11b4330a7b946e61e8e1d8a89f1f`。

1. 右侧和新左侧均保持现有固件、继续供电；Dongle保持连接电脑。
2. 从Dongle设备页FLASH双重确认进入NICENANO，运行：

   ```bash
   cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-dongle-left-slot-recovery.uf2' /Volumes/NICENANO/
   ```

3. 首次检查期间split连接暂缓。确认并清理旧槽后会自动重启一次；等待约10秒，再上滑设备页查看结果。
   新裸左侧继续USB供电，给自动发现/配对约60秒。无需在电脑蓝牙设置配对。
4. **LEFT CLEARED + K1 ON/K2 ON**：定向清理和双连接已通过本次实机观察，继续测试右侧轨迹球。
   若LEFT CLEARED但K2仍--，说明旧槽已处理，仍需进一步检查新左侧的供电/身份/配对状态，不能继续猜测槽未清。
5. 可在确认结果后从设备页刷回日用r2；地址和配对修复会保留：

   ```bash
   cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-dongle-scan-policy-r2.uf2' /Volumes/NICENANO/
   ```

不要刷settings_reset，也不要重刷右侧或清除全部配对。

| 设备页结果 | 含义 / 下一步 |
|---|---|
| LEFT CHECKING | 初次检查尚未完成；通常只持续数秒 |
| LEFT CLEARED | 已有完成记录：旧K2地址与精确对应密钥已清理，并核对K1持久化地址/密钥未变；后续启动不会再次清理 |
| LEFT SLOT EMPTY | **首次检查时**槽位已空；记录一次性无操作决定，不删除任何配对。新左侧加入后仍显示这个历史检查结果 |
| RIGHT NOT FOUND | 无法确认要保护的K1地址、内存绑定或持久化密钥，拒绝操作 |
| BAD SLOT DATA / SLOT CHANGED | 数据格式异常、左右地址相同，或待恢复事务的身份已变化，拒绝清理 |
| STORAGE ERROR / UNPAIR ERROR / VERIFY ERROR | 写入/删除/回读验证失败；停止后续处理并保持split发现禁用，防止错误配入 |

遇到错误时记录整页结果，从仍可使用的触屏FLASH入口刷回r2。维护错误期间不连接键盘是刻意保护，
不等于已删除右侧配对；恢复日用r2后验证右侧重连，再针对错误继续处理。

## 实现与边界

- 仅显式启用 `PROSPECTOR_LEFT_RECOVERY=true` 的普通Touch modes构建加载维护conf；日用配置默认关闭。
- 在固定central的 `finish_init` 处暂缓transport available，防止检查/清理时任何split外设配入或连接。
  在低优先级队列延后2秒运行；Settings读操作会等待完整load/commit释放锁，2秒也避开Bootloader双复位窗口。
- 保护槽固定为0，目标槽固定为1；编译断言双槽、左显示映射1及默认BT identity配置。
- 必须读到有效K1地址与现存bond。删除前读取K1持久化密钥，删除后逐字节核对该地址和密钥仍相同。
  密钥只在RAM中临时比较，不输出、不导出、不写进事务记录。
- 仅向 `bt_unpair(BT_ID_DEFAULT, &old_left)` 传入旧K2的具体身份；从不传NULL/ANY，也不调用全局reset。
  [Zephyr API](https://docs.zephyrproject.org/latest/doxygen/html/group__bt__gap.html)明确NULL/ANY表示清全部，代码和测试均禁止该路径。
- 精确删除 `ble/peripheral_addresses/1`；移除对应旧设备的密钥/缓存。其余profile、设备身份、亮度等不修改。
- 在 `prospector_left_repair/v1` 中持久化20字节的身份绑定事务记录。先写并回读intent，再做删除。
  `bt_unpair`可能吞掉持久化删除错误，因此还要确认后端旧密钥已消失、内存bond也已移除。
- 完成后写并回读一次性完成记录，再重启，重新加载central私有地址数组。
  本来为空的情况也会写完成记录，避免新左侧配入后下次开机被误当旧设备。
- 中途断电可仅针对原身份继续；发现K1或目标身份已改变时拒绝继续。出错不开放split扫描，不产生重启循环。
- 完成记录存在后，每次启动只恢复正常扫描策略，不再删除新配入左侧。以后再次更换左侧需另行明确发起维护。
- 扫描策略仍为r2；右侧800 CPI/ATT3/8ms、键位、GPIO和左右UF2不变。右侧刷写文件与r2文件SHA核对保持原值。

## 本地验证与待验收

- 实际维护C、实际生成central finish_init、固定Zephyr key编码器的native联合测试：PASS。
  覆盖精确删除、K1地址/密钥保留、重复启动、新左侧配入后重启、空槽一次性保护、部分失败重试、
  身份变更、异常长度、读取/写入/删除/解除绑定失败、持久化密钥删除静默失败和工作队列调度失败。
- 实际LVGL设备页、模式页、双重确认和120次切屏状态回归（无硬件副作用mock）：PASS。
- 维护版Docker/west：PASS；FLASH503328B、静态RAM216578B；UF2末端0xA0F00，旧Bootloader限额余49408B。
- 实际ELF BLE→central→observer初始化顺序：PASS。
- 普通构建默认关闭维护：PASS；应用payload除SOURCE/构建时间外与用户已验收r2逐字节一致。
- 未自动刷写硬件。用户已确认 LEFT CLEARED、K1/K2 ON；修复后双连接手感及完整左侧矩阵仍待验证。

构建清单：`releases/T5-11/prospector-dongle-left-slot-recovery.json`。
日志：`firmware/build/reports/left-slot-recovery-build-final.log`、`left-slot-recovery-native.log`、
`left-recovery-ui-tests.log`、`left-recovery-disabled-build.log`。
本地工作树含未提交维护实现；未运行远程CI，不冒充原固定module提交已包含此功能。

```bash
PROSPECTOR_LEFT_RECOVERY=true PROSPECTOR_BUILD_NAME=prospector-dongle-left-recovery PROSPECTOR_KEYMAP=touch_modes SKIP_WEST_UPDATE=true bash firmware/docs/prospector-touch/scripts/build-touch-only.sh
python3 module/tools/test_left_slot_recovery.py
```

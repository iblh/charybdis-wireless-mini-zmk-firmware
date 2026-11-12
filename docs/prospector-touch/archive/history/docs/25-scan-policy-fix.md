# T5-09：连接数量驱动的扫描策略候选

> **实机回归，停止使用此版。** 用户确认 T5-09 屏幕正常但右侧无法连接，仅回退 T5-08 后恢复。
> 已定位生成 central 编译单元改变链接顺序，导致其 Settings 回调在 BLE 初始化时被清除。
> 下文保留原交付记录；后续修复与新文件见 [T5-09B 启动顺序修复](26-scan-startup-regression.md)。

## 实现范围

T5-08 实机 ABBA 确认单侧在线时快速后台扫描造成主要周期性空档。用户授权只更新 Dongle。
本候选接入普通构建，开机常驻，不依赖串口命令、80秒实验或每次手动暂停。
右侧不重编、不刷写，保留用户当前 800 CPI / ATT3 / 8ms / 顺时针15°。

| 状态 | 策略 |
|---|---|
| 没有外设在线 | 原快速被动扫描，30ms窗口 / 60ms间隔 |
| 一侧在线、另一侧缺席 | 被动扫描5ms窗口 / 200ms间隔，持续自动发现 |
| 双侧在线 | 停止扫描 |
| 正在发起连接 | 暂停扫描，完成/失败回调后重评 |
| split transport 被禁用 | 停止扫描 |

保留两外设槽、64项中央队列、7.5ms interval / latency30、PHY、键位、显示/触控/背光GPIO和绑定。
5ms/200ms 是首个待实机验收参数，不能从本地测试就认定既达到关扫描效果又有理想发现速度。
低占空比可能延长第二侧发现时间；不能承诺与原50%扫描一样快。

## 代码与普通构建

- module 中 `split_scan_policy.h` 与 `split_scan_policy_impl.h` 管理连接数量决策、扫描模式与重试。
- `PROSPECTOR_SPLIT_SCAN_POLICY` 由 touch.conf 启用，普通 Touch 构建和具备同一模块源码的 CI 都走模块 CMake。
- CMake 从固定 central.c 生成构建目录中的副本，只替换原扫描函数及连接发起失败的清理路径；
  原 BLE central TU 标记为 HEADER_FILE_ONLY，确保只编译生成的一个实现。
- 完整源文件 hash 校验固定4dd95d7版本；遇到未知/改动过的 central.c 直接构建失败，不静默失效。
- 原 West checkout 不修改；普通构建使用只读 sibling module，不再复制覆盖另一份模块工作副本。
- source ID 包含生成器和策略头文件，生成的central与原central校验值写入清单。
- 扫描调用仅在模式变更时发生，不跟随每个按键/轨迹球事件启停。
- 非阻塞mutex避免在输入/BT回调中等待其他扫描操作；API临时失败交由现有低优先级队列约1秒后重评；该队列预留1536B栈空间。
- 停止扫描失败时释放尚未发起的CONNECTING槽，避免占住槽后永远无法重新发现。
- 原T5-04..08 diagnostics通过pipeline.conf显式关闭新策略，保持历史基线含义；原UF2不覆盖。

本次修改包含尚未提交的两仓库工作树；远端west模块仍固定旧提交。
本地构建已使用当前模块源码验证，未运行GitHub CI。发布到远端前需提交模块并更新对应pin，不能宣称远端已通过。

## 交付与本地验证

文件：`firmware/build/prospector-dongle-scan-policy.uf2`，**只刷 Dongle**。
设备页标识：`T5-09-SCAN`，SOURCE `20BD12`。

- 本地普通 Docker/west 单目标构建 PASS。
- FLASH 501672B；静态RAM 213442B；UF2 `0x26000–0xA0800`，旧Bootloader限额余51200B，PASS。
- 实际构建仅编译generated BLE central，未重复编译原文件，原West文件hash保持不变。
- 实际keymap、ST7789、触控、pinctrl与split-input节点和T5-08相同。
  普通构建使用原studio-rpc-usb-uart snippet、Studio仍禁用；不再附加诊断profile/串口控制。
  DTS因此有不同的CDC chosen节点和额外未使用行为节点，未声称整份DTS逐字节相同。
- native直接编译实际策略与生成的连接发起函数，覆盖0/1/2侧、连接中、连接失败、
  停扫描失败不占死槽、已有扫描由慢转快、锁竞争、失败重试、传输禁用、调用中状态变化和EALREADY恢复。
- pipeline/cadence/扫描AB历史回归通过；无物理自动刷写。

**实机仍待验收：** 持续滚球、打字/UI并发、真实发现/重连，以及低占空比是否仍有颗粒感。
双侧状态机通过本地测试不等于两侧键盘实机已经通过。

## 刷写和最简验收

让 **Dongle** 从设备页双重确认进入NICENANO，再运行：

```bash
cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-dongle-scan-policy.uf2' /Volumes/NICENANO/
```

右侧无需更新，继续当前固件和供电方式。先直接验收，不要求新一轮完整串口采集：

1. 设备页确认 `T5-09-SCAN`；等右侧自动连接。
2. 中速/慢速滚球各约15秒，快速打字约15秒，再同时滚球和打字约15秒；确认周期性停顿是否改善。
   顺便切一次status布局，确认显示与触控正常。
3. 保持Dongle连接电脑，右侧彻底断电约5秒再上电，确认自动重连、打字和轨迹球恢复。
4. 若左侧现已可用，开机确认能自动加入，再分别断开一侧观察另一侧仍正常；
   若未组装，记录“双侧实测待验”，不要求现在装配。

反馈只需：版本标识是否正确、滚球改善程度、是否丢字、右侧是否自动重连，以及仍有的异常。
若长时间不能重连，保留现象后可回退旧Dongle文件；不要清除配对。

回退：`firmware/build/prospector-dongle-scan-ab.uf2`（T5-08，正常启动恢复原快速扫描）。

## 复现

从工作区根目录：

```bash
PROSPECTOR_BUILD_NAME=prospector-dongle-scan-policy PROSPECTOR_KEYMAP=touch_modes SKIP_WEST_UPDATE=true bash firmware/docs/prospector-touch/scripts/build-touch-only.sh
```

native测试：`python3 module/tools/test_scan_policy.py`（需要可用本地C编译器）。
产物哈希、源文件快照与构建参数见 `releases/T5-09/`。

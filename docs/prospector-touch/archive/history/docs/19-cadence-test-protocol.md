# 2026-11-01：1600 CPI 后仍有颗粒感的帧间隔测试

用户已刷右侧 1600 CPI，并调低 macOS 跟踪速度，慢速移动仍有颗粒感。
这是问题尚未解决的实测结果，不将提高 CPI 标为修复。保留 1600 CPI 作为本轮固定基线，
不在换 Dongle 时同时回退 CPI 或改变主机速度/加速度。

## 网页截图的解释

已读取用户页面 `https://input-test.nxtkb.com/` 及当时实际脚本
`/assets/index-DQeZv1UX.js`，脚本 SHA-256：
`9a0f98e1d2f32368ff2b26de0cf53693f57b3f7ac5e62d34fc19604bc0198511`。

Event diagnostics 的 delta timeline：x 是最近四秒时间；y 是每个浏览器事件
`Math.hypot(movementX, movementY)`，单位 px。它不是二维指针轨迹，也不按事件间隔归一成速度。
Rate 是最近 2500ms 的浏览器事件数 / 2.5；停手会拉低这个数。普通模式走 pointermove，
锁定指针模式走 mousemove；当时脚本没有 getCoalescedEvents 调用。

截图中两段的位移变化明显不同，可以支持“输出手感不同”，但不能从折线本身证明
硬件报告率低、断流或某个固定延迟。轨迹球手指用力/换手、滚球静摩擦、实际计数、
报告节奏、系统指针处理和浏览器合并事件都可能改变此图。
两种设备的 DPI、同样动作的物理速度也尚未匹配，不能把 Razer 曲线当作固件必须复刻的波形。
参考：[Pointer Events 合并事件](https://www.w3.org/TR/pointerevents3/#coalesced-events)。

## 固件与连接

只刷屏幕 Dongle：`firmware/build/prospector-dongle-pipeline-q64-cadence.uf2`。
SHA-256 `8a857e1d02c95104f95f7cb539725630095967db64d53758d9accba160715be6`。
旧 Bootloader 范围核验通过：`0x26000–0xAA400`，余 11264B。
本地构建/测试通过，当前仍待实机验收。原 q64 回退文件保留。

右侧保持 `prospector-right-profile-8ms-angle15-cpi1600.uf2`，不用重刷。
保持 MAC-DV、当前 macOS 跟踪速度/加速度、同一浏览器及网页模式/缩放。
本轮不测试鼠标键、拖拽或滚轮。

先退出占用串口的 screen 或旧采集器，再用 Dongle 设备页双重确认进入 NICENANO：

```bash
cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-dongle-pipeline-q64-cadence.uf2' /Volumes/NICENANO/
```

重启后设备页应显示 `T5-05-TIMING`、SOURCE `9AF40F`。
Dongle、右侧都通过数据线连接电脑；右侧输入仍通过 BLE 到 Dongle。
等约 15 秒，再用插入右侧前后 `ls /dev/cu.usbmodem*` 的结果确定各自串口。

## 两个终端采集

以下端口仅沿用上轮示例，必须按实际设备确认。

终端 A（Dongle）：

```bash
DONGLE_PORT='/dev/cu.usbmodem21201'
PROSPECTOR_ROOT='/Users/paul/Workspace/Lab/prospector-pro'
DONGLE_LOG="$PROSPECTOR_ROOT/firmware/build/reports/dongle-cadence-$(date +%Y%m%d-%H%M%S).log"
python3 "$PROSPECTOR_ROOT/firmware/docs/prospector-touch/scripts/capture-right-profile.py" \
  --port "$DONGLE_PORT" --output "$DONGLE_LOG" --seconds 150
```

终端 B（右侧，尽量在几秒内启动）：

```bash
RIGHT_PORT='/dev/cu.usbmodem21101'
PROSPECTOR_ROOT='/Users/paul/Workspace/Lab/prospector-pro'
RIGHT_LOG="$PROSPECTOR_ROOT/firmware/build/reports/right-1600-cadence-$(date +%Y%m%d-%H%M%S).log"
python3 "$PROSPECTOR_ROOT/firmware/docs/prospector-touch/scripts/capture-right-profile.py" \
  --port "$RIGHT_PORT" --output "$RIGHT_LOG" --seconds 150
```

确认 Dongle 输出 `CAD stage=RX` 和 `CAD stage=USB`，右侧输出 `STATE/RAW/PIPE/LINK`。
若只有普通 RX/USB 行、始终没有 CAD，先核对设备页版本，不急着做整轮测试。
两端都有输出后开始手机计时；不要求不同设备 uptime 相等。

## 120 秒动作表

在同一浏览器打开测试网页，保持前台和同一种指针模式；不在测试中开关“精确模式”。
停止操作 Razer，除指定对照阶段外不要移动它或触碰 Mac 触控板。

| 时间 | 操作 |
|---|---|
| 0–10s | 轨迹球、Razer 都静止 |
| 10–40s | 只滚球，尽量连续、均匀的中速长行程或小圆，避免频繁停手；记录必要的停手/换指时间 |
| 40–70s | 只滚球，复现慢速精细移动的颗粒感；刻意反向/停手也记时间 |
| 70–80s | 两者静止 |
| 80–110s | 只移动 Razer 作网页对照，轨迹球保持静止；Dongle 日志不记录 Razer 的报告，这是预期 |
| 110–120s | 两者静止，观察有没有延后位移 |

此后等两端 150 秒自动结束，不按 Reset、不拔插 USB、不切 status 布局。
中速和慢速阶段应分别截一次完整的 Event diagnostics（含 Rate/Avg/P95/Peak）；
Razer 单独截图，至少持续移动五秒再截，不把两种设备混在同一个四秒图里作为唯一证据。
截图动作造成的停手不作为固件断流，记录在现象描述中。

回传两份日志，注明明显颗粒/跳动阶段与时间、浏览器、屏幕刷新率（知道才填）、
网页是否锁定指针。不要求安装抓包软件或新鼠标驱动。

## 数据判断边界

- RX：已识别的 input-split sync 帧到达 Dongle 的节奏，包含上游采样/调度/无线影响。
- USB：本地鼠标 HID 端点成功接受提交的节奏，不是主机实际收到或屏幕绘制的时间。
- 两边均有集中短间隔后接较长间隔：提示节奏在进入 Dongle 前已不均匀，仍需结合右侧采样。
- RX 较均匀而 USB 更不均匀：优先看 Dongle input/HID 调度和等待。
- 两边较均匀但仍颗粒：继续看每帧位移量化、主机指针增益及物理追踪，而非盲目提高频率。
- 最大 gap 包含停手；慢速时不是每个报告周期都有非零移动，因此帧数低不自动等于故障。
- 所有图和日志均不能单独证明无线丢包，也不能把 8ms 配置直接当作稳定测得的 125Hz。

本轮先定位，不把插值或平滑滤波当作修复来掩盖不均匀输出。

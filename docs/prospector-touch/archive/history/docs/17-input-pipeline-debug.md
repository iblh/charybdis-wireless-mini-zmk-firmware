# T5-04 — 输入卡顿、方向校准与仓库清理

## 当前事实（2026-10-31）

用户刷入 T5-03 的右侧 8ms / 顺时针 15° 候选后，纵向大致正确，但横向仍希望
再顺时针约 25°；连续运动仍有延迟/跳跃，快速打字也会明显延迟甚至缺字。
用户补充：目前只组装右侧，球静止时似乎也丢字，左侧暂不能参与测试。
两份现有采集文件都只有主机生成的文件头，没有设备字节；直连 USB 对比尚无结果。
这次不能把症状归因于光学安装，也不能宣称通过改角度或加大队列已修复。

## 已确认的源码问题与边界

1. 固定 ZMK `4dd95d7` 的 `src/split/bluetooth/central.c` 使用同一个
   `peripheral_event_msgq` 接收键位、轨迹球和其他状态事件，容量默认 **5 项**。
   七个生产位置调用 `k_msgq_put(..., K_NO_WAIT)`，未检查失败；键位通知处理还会先
   更新保存的位图，因此队列满时某个键的按下/释放变化可能永久丢失，直至再次变化。
   这是可触发的丢事件路径，但尚未实测证明它是本次丢字的原因。
2. Operator WPM 的 33ms `k_work` 在系统队列直接调用 LVGL；三个布局的输出状态
   订阅也直接改界面，Classic/Field 的延时动画在系统队列调用 LVGL。
   当前使用独立显示队列，这些访问没有统一串行。已把 WPM 改为 LVGL timer，
   输出订阅改为 `ZMK_DISPLAY_WIDGET_LISTENER`，相关延时任务提交到显示队列。
   本地真实 LVGL 回归通过；并发竞态在主机单线程测试中不能被完全复现。
3. 外设的键位与轨迹球 GATT 通知共享一条 service 工作队列；运动发送回调一直
   drain 到空才返回。如果 BLE 吞吐不足且运动队列持续被填入，键位通知工作可能
   等待过久。此为代码审查风险，是否发生需看右侧 TX 日志。
4. USB HID 会等待信号量最多 30ms，但原代码不检查 `k_sem_take` 结果就继续写端点。
   诊断版统计超时和写失败，**暂不改变发送策略**，以免把尚未定位的问题换成另一种丢报告。
5. MAC-DV / WIN-DV 的主行 hold-tap 为 280ms，并有 150ms prior-idle 和异手触发规则；
   个别字母的延后输出可能是判定时间，但不能解释为“允许缺字”。对比 GAME（无主行
   hold-tap）有助于区分传输拥塞和键位策略，不在这次改变习惯键位。

参考：[ZMK split 配置](https://zmk.dev/docs/config/split)、
[LVGL 9.2 多线程约束](https://docs.lvgl.io/9.2/porting/os.html)。
实际行为以本地固定 SHA 的源码为准。

## 候选与使用顺序

下列候选只用于诊断，保持原配对资料、GPIO、800 CPI；不自动刷机。
其中 RIGHT TEST 单独改变四个 NAV 鼠标入口，其余候选保持原模式键位。
左侧不需要刷。刷写目标必须分清。

| 名称（`firmware/build/`） | 刷入目标 | 差别 |
|---|---|---|
| `prospector-dongle-pipeline-q5.uf2` | 屏幕 Dongle | 原 5 项接收队列，UI 线程修正，新增 RX/USB 统计 |
| `prospector-dongle-pipeline-q64.uf2` | 屏幕 Dongle | 同上，仅中央接收队列改为 64 项 |
| `prospector-dongle-pipeline-q64-right-test.uf2` | 屏幕 Dongle | q64 加右侧可操作的鼠标入口，设备页键位标签 `RIGHT TEST` |
| `prospector-right-pipeline-8ms-angle15.uf2` | 右键盘 | 保留 15° / 8ms，新增外设发送链路统计 |
| `prospector-right-pipeline-8ms-angle40.uf2` | 右键盘 | 同上，仅总旋转改为 40°，用于方向对照 |

**先只刷 Dongle q5，保留右侧当前 8ms。** 这能先观察集中接收、USB 输出和 UI 修正后的情况。
然后 Dongle q64 重做相同操作。若 q64 明显改善但队列仍接近上限，不能只靠继续加大队列；
需要找出消费者长时间停顿的来源。若仍有问题，再刷右侧 angle15，同步记录两端。
角度 angle40 放到性能对比之后，避免同时改变多个变量。

只有右侧时可先用 q64-right-test 完成鼠标操作；其基础 MAC-DV/WIN-DV/GAME、
主行 hold-tap 和其他层均未修改。需要严格对比 q5/q64 性能时，两份原键位版仍保留。

进入所需板子的 NICENANO 后，例：

```bash
cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-dongle-pipeline-q5.uf2' /Volumes/NICENANO/
```

已保留回退：Dongle `prospector-touch-peripheral-sync.uf2`（T5-02）及
`prospector-touch-input-modes.uf2`（T5-01），右侧 `prospector-right-profile-8ms-angle15.uf2`
及原正常外设 `prospector-touch-right-peripheral.uf2`。不要把任何右侧文件刷到 Dongle。

## 当前零输出问题

旧版采集器只写入 `# port=...` 就等待读取；这行属于主机文件头，不是设备日志。
文件名里的 `12ms`/`8ms` 也不会改变板子的固件或采样率。
本次在用户给出的 `/dev/cu.usbmodem21201` 实际短时读取两次（6s/4s），均为 0 字节；
第二次确认主机报告 DTR/RTS 均为 True。未向串口写入数据，未复位/刷机。
这不能确定板上的镜像，也不能证明 logger、工作队列或串口设备正常。

采集器现在会记录握手读回、结束原因、实际时长和字节数；15s 无字节会警告，
全程无数据以 exit code 3 退出。增加了真实 pseudo-terminal 零输出测试。
后续用户确认：该端口实际是 **Dongle**；右键盘只插充电器，没有 USB 数据连接到电脑。
因此此前没有采集到右侧的 PMW 日志，不能据此判断右侧 logger/系统工作队列故障。
右侧日志不经 BLE 转发到 Dongle。下一次必须用数据线把右键盘也接到电脑，
保持 Dongle 连接，比较插右侧前后的端口列表；再选择新增端口。

## 收集日志（每个版本一次 90 秒）

退出占用串口的 `screen`：`Ctrl-A`，再 `\`，确认退出；关闭窗口可能仍保留串口占用。
诊断日志在运行中会持续输出，无需抢开机瞬间。先只连接 Dongle 确定其串口，之后连接
右侧再找新增端口，避免两端混淆。右侧通过 USB 只供电/输出日志，输入仍经 BLE 到 Dongle。

```bash
ls /dev/cu.usbmodem*
mkdir -p /Users/paul/Workspace/Lab/prospector-pro/firmware/build/reports/input-lag
python3 /Users/paul/Workspace/Lab/prospector-pro/firmware/docs/prospector-touch/scripts/capture-right-profile.py --port /dev/cu.usbmodemXXXX --seconds 90 --output /Users/paul/Workspace/Lab/prospector-pro/firmware/build/reports/input-lag/dongle-q5.txt
```

把 XXXX 换成实际端口。q64 换文件名 `dongle-q64.txt`，采集器拒绝覆盖已有文件。
需要双端时另开终端，用右侧端口写到 `right-a15.txt`；不要两个程序同时打开同一个串口。
日志只记录计数、耗时、光学质量、位移合计和连接参数，不打印字母/键码/设备地址。

仅右侧组装时，每次 90 秒按顺序：

- 0–20s：球静止，快速重复右侧最上排五个字母（MAC-DV 为 F/G/C/R/L，不含 hold-tap）。
- 20–40s：球静止，重复右侧主行字母 D/H/T/N/S（包含 hold-tap），比较延后/缺字。
- 40–60s：只连续滚动球，尽量匀速，不按键。
- 60–75s：同时滚动球和打字。
- 75–90s：切 Classic/Field/Operator，同时重复输入与滚球。

在临时文本中测试，并记录大概在哪段出现缺字/停顿。左侧组装后再增加两侧同时输入。
可额外在 GAME 模式重复相同物理键的静止球打字，
比较是否仅 MAC-DV 出现问题；再用 Dongle 直接接 Mac 做一次对照，记录有无 USB 切换器/扩展坞。
不需要删除蓝牙配对，也不要 settings_reset。

## 日志如何判断

统计每两秒清零；每行是该窗口计数或最大值，两个端口的窗口没有自动同步。

| 字段 | 意义及限制 |
|---|---|
| RX `key0/key1` | 收到的键位变化数量，按当前 BLE 配对槽编号，不是左右固定命名 |
| `drop_key/drop_point/drop_other` | Dongle 中央接收队列入队失败次数；`drop_key>0` 是直接丢键证据 |
| `high` | 入队后采样到的队列深度高水位；消费者并发读取时可能低估峰值 |
| `age_us` | 已出队事件从入队到处理的最大时间；32-bit 周期计时，不适用于极长挂起 |
| `handle_us/handle_err` | 单个事件处理最大耗时/负返回次数；包括下游 input queue 入队失败等 |
| `sys_late_ms` | 系统工作队列 100ms 心跳的最大迟到，不是无线延迟 |
| USB `key/mouse/other` | 进入 USB 发送函数的报告次数，包含失败尝试 |
| USB `key_down/key_up` | 键位行为产生的键码事件数，不含键码内容；与 RX 对比辅助区分 hold-tap 判定与传输问题，不保证与物理按键一一对应 |
| `sem_timeout/wait_us/err` | HID 信号量超时/最大等待/USB 路径错误；不等于主机收到的报告数 |
| `mouse_err/mouse_send_us` | 鼠标输入监听器调用 endpoint 的错误/最大耗时 |
| TX `key/point`、`*_err` | 外设尝试 GATT notify 的次数及失败；成功只表示本地协议栈接受 |
| `key_full/point_full` | 外设消息队列入队失败次数；`queue_wait_us` 可揭示 100ms 排队等待 |
| `notify_us` | 单次 GATT notify 最大耗时；结合 key_full 判断共享发送队列压力 |
| PMW `RAW/PIPE` | 原光学质量、SPI/input 错误、传感器工作等待，含义见文档 16 |
| LINK | 实际连接 interval / latency；`slot_index` 是连接对象索引，不是左右标识 |

没有任何错误计数也不能证明端到端可靠：日志没有主机 HID 抓包，不能判断主机调度、
无线重传、失去光学纹理或用户实际按下次数。只有稳定复现后，才决定是否拆分接收队列、
限制单次运动通知 drain、调整 USB 报告调度或 hold-tap。不要一次改变所有参数。

## 方向测试

先记住 angle15 的表现，再试 angle40：各做 5 次纯向前、向右，观察**指针**的方向。
40° 是总角度，不是叠加到另一个运行时角度；保留定点小数余量。
如果横向改善、纵向明显变差，说明不能用同一个刚性旋转同时校正当前两种手势。
此时需要两轴原始运动合计/实际轨迹来判断手势和球面几何，不能再反复累加角度。
本轮不加入每轴独立剪切，也不把屏幕指针校准和页面滚轮正反混为一谈。

## MAC-DV 现有鼠标操作（当前键位未改）

**原键位需要左侧，因此当前只有右侧无法使用左拇指入口。**
若刷入 q64-right-test，在 MAC-DV 下先按住右拇指外侧 **Space/NAV** 超过约 200ms，
确认屏幕显示 `M/NAV`，保持按住后：

| 右侧测试版动作 | 再操作哪个键 |
|---|---|
| 左键/拖拽 | 右拇指内侧 Enter/SYM；按住并滚球即拖拽 |
| 右键 | 右键盘最上排最外侧 Backspace 位置（第 6 列，不是字母 L） |
| 页面滚动 | 按住右键盘主行最外侧 Enter 位置，滚动球，屏幕 `M/SCRL` |
| 慢速指针 | 按住右键盘最下排最外侧 Shift 位置，滚动球，屏幕 `M/SLOW` |

只在 NAV 更改 11/23/35/39 四个位置；原来该层的 Delete、Enter、Shift、Enter
分别被以上操作替代。松开右拇指外侧后回到原基础层；请先松开其他按住的键再松 NAV。
右拇指基础层 Space 和 Enter 仍可正常轻点使用。

以下是左右完整组装后的**原版键位**：

按正常打字姿势、从外侧到内侧：左拇指三个键为 **Esc/FN、左键、Backspace/NUM**。
右拇指两个键从内侧到外侧为 **Enter/SYM、Space/NAV**。键帽文字可能不对应固件。

| 动作 | 操作 |
|---|---|
| 左键 | 左拇指中间键，按住并滚球可拖拽，双击就是连按两次 |
| 右键 | 按住左拇指最外侧 Esc/FN 超过约 200ms，确认屏幕 `M/FN`，再点右拇指内侧 Enter/SYM |
| 页面滚动 | 按住上述 FN，再按住左拇指中间键，确认 `M/SCRL`，同时滚动球；松开中间键恢复指针 |
| 精细移动 | 按住 FN，再按住左拇指内侧 Backspace/NUM，确认 `M/SLOW`，同时滚动球 |

FN 要先成立再按第二个键；直接在基础层按右内侧是 Enter，不是右键。
鼠标中键 MB3 尚未绑定。页面滚动使用轨迹球模式，不要求按下球体；
滚动正反另受系统“自然滚动”设置影响。[ZMK 按键定义](https://zmk.dev/docs/keymaps/behaviors/mouse-emulation)。

## 本次清理范围

删除工作区、firmware、pcb 中的 3 个 `.DS_Store`，及两份旧 PMW 初始化诊断的
可再生构建目录 `build/prospector-right-trackball-diagnostic`、`build/prospector-right-trackball-delay1s`。
删除前保留各自 UF2/ELF/map/.config/zephyr.dts 到 `build/reports/t5-04-cleanup/`；
原顶层回退 UF2、历史日志仍在。原目录合计约 109MB，保存证据后净回收约 92MB（十进制）。
清理清单为该目录 `manifest.json`。

保留所有未提交源码、PCB 制造文件、West 依赖、原 CI 证据、旧版本清单与构建脚本。
这些不能仅因“旧”就认定无用。本轮不删除历史归档或更改依赖 SHA，不提交/推送未验收候选。

## 新反馈：USB 显示 100，电池显示 8

这些数字是右侧通过 BLE 上报的百分比，不是轨迹球速度。当前 nice!nano v2
配置使用 `zmk,battery-nrf-vddh`，测的是 nRF52840 的 VDDH 电源输入，
再按固定 ZMK 电压曲线估算百分比。这里不是独立电量计，也没有充电器状态反馈。
源码中约 3.50V 会给出约 8%，≥4.20V 会饱和为 100%；这是**采样点**电压的换算，
不能直接等同电池两端实际电压。在电源切换电路把 USB 电压送到采样点时，
插 USB 后的 100% 可能只说明由 USB 供电，不能证明电池充满。

右侧当前报告间隔 60s，但进入 IDLE/SLEEP 会暂停采样，回到 ACTIVE 再启动。
因此充电时长和 UI 显示不能单独判定充电器工作。需要确认电池为单节可充锂电池、
正负线分别接在哪个接口/焊盘，以及拔 USB 后电池两端的手动 DC 电压；
再对照主控 B+ 对 GND 的电压判断接线、开关是否隔离充电路径和兼容板采样差异。
目前没有该兼容主控的原理图，不把官方 nice!nano 的充电电路当成这块板的已知事实。

参考：[ZMK 电池采样](https://zmk.dev/docs/config/battery)、
[官方 nice!nano 电池连接要求](https://nicekeyboards.com/docs/nice-nano/getting-started/)。
未更改采样比例/百分比曲线，也未建议通过反复刷机或延长充电来掩盖问题。

后续用户确认：3.7V 电池插在 Nano Holder，拔 USB 后直接测得 **3.5V**。
这与约 8% 估算一致，当前不需要“校正成 100%”。
核对用户 Gerber X2 的明确连接（F_Cu/B_Cu 两面一致）：

```text
右侧电池插座 J6.1 (bat_sw_r) → SW4.3
SW4.2 (bat_r) → 右主控 U2.24 RAW
J6.2 → GND
SW4.1 未连接
```

**该电池开关也会切断电池到主控的充电路径。** 关掉开关时，即使 USB 让键盘工作、
显示 100%，电池仍可能完全与主控充电器隔离。若走的就是 J6 插座，充电测试需开关
处于接通电池的 ON 位置；不是关机后充电。此结论来自 PCB 网络，仍需排除开关焊接不通。
主控自身是否存在/正常运行充电器尚不能仅由兼容引脚名称确认。

下一步保持开关 ON，用手动 DC 档比较 J6 电池正端对 GND、主控 RAW/B+ 对 GND，
两者应接近（开关接通且走线正常）。若不接近，先查开关/插座/焊接；若接近但充电后
拔 USB 的电池电压仍长期约 3.5V，再核对兼容主控的充电芯片/指示灯和产品资料。
不要用 VCC 3.3V 代替电池端电压，也不通过改固件百分比掩盖充电问题。

## 2026-11-01：首次有效右侧 8ms 日志分析

来源：`firmware/build/reports/right-profile-8ms-01.log`，SHA-256
`ef1a99a606182a37fffb464f7be6e8c08fc183e331ab29f49c117baa13e232c2`。
实际端口 `/dev/cu.usbmodem21101`，采集器尾注显示 56.1s、23737 个设备字节后手动停止；
不是完整 90s。保留原文件，派生统计为同目录 `right-profile-8ms-01-analysis.json`。

- `PMW3610 initialized`；可见完整 STATE 为 ready=1、step=4、err=0、8ms、15°。
  先前产品 ID 0xFF 的初始化失败没有在这份日志里出现。
- 连续的新运动片段（设备 uptime 2:56–3:42）的 24 个两秒窗口共 7888 次采样；
  SQUAL 最小/最大为 128/158，按窗口样本数加权的均值约 148.54（日志均值为整数，故近似）。
  sq0=0。没有持续零质量的证据，但质量只在已取得的 burst 上统计，不能排除无采样间隙失追踪。
- 可见 SPI 读错误、传感器到 Zephyr input 入队错误均为 0，IRQ→work 最大等待 1ms。
  这里只覆盖传感器前段，不覆盖之后的 GATT 发送、Dongle 接收、USB HID。
- 多个窗口约 488–496 次采样/2s，符合约 4ms 的传感器采样。8ms 是**最小报告间隔**，
  不是强制每 8ms 发包；X/Y input_events 也是分开的事件数，不能当作鼠标报告频率。
- `LINK interval_us=7500 latency=30` 表示 7.5ms 的连接间隔及 peripheral latency=30。
  后者不是固定 30ms 延迟或丢包数。固定 Zephyr 源码在有外设 TX 入队时调用
  `ull_periph_latency_cancel()`。是否需要 latency=0 对照，应在队列/USB 日志后单独测试。
- `gap_ms=173046` 是前后运动样本跨长静止时段的间隔；另有 105–494ms 和 2652ms。
  gap 也包括主动停球，尚需用户说明是否真正持续滚动，不能直接当作 USB/BLE 延迟。
- 文件开头混有较早开机信息、23 条重复 profile 行、一个时间回跳及一条截断 PIPE。
  时间顺序不干净，可能含串口/日志缓冲残留；不能据此断言设备重启或复位循环。
  新运动片段的记录本身按时间递增。

用户后续确认：实际是滚几下停一下，采集期间未按 Reset、未拔插 USB。
因此这些 gap 不能作为持续滚动卡顿的证据；开头旧记录更应按可能的缓冲残留处理，
不把时间回跳直接解释为用户重启，也尚无充分证据证明自动重启。

用户暂不测鼠标按键/拖拽，因此下一步建议刷 **原键位 q64 Dongle**，右侧先保留
目前 8ms 固件；不要求 RIGHT TEST。q64 同时包含已经本地验证的 UI 线程修正与链路计数，
但这份右侧旧日志不能证明它已解决丢字。需要 q64 的 RX/USB 日志，后续若仍有问题
再考虑右侧 pipeline 版的 TX 计数。

USB/BLE 高亮来自 `zmk_endpoint_get_selected().transport`，表示 **Dongle→电脑** 的
输出通道。当前链路是右键盘→BLE→Dongle→USB→电脑，故 USB 高亮正确；
它不是“键盘是否通过 BLE 连接”的指示灯。不需要为了两者同时亮而切换 OUT_BLE。
参见 [ZMK 输出选择](https://zmk.dev/docs/keymaps/behaviors/outputs)。

本轮保持 800 CPI、8ms、15°：CPI 决定单位物理位移的计数，不修复排队、USB 等待或丢字。
先解决输入可靠性，再在固定其他变量时试 1200/1600 CPI，并协调主机指针速度。
不要同时改变 CPI、旋转、报告间隔、BLE latency，从而失去可比较的基线。

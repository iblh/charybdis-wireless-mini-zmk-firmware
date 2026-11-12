# T5-07：ATT 缓冲等待与本地发送完成诊断

**2026-11-01 实测更新：** ATT8 减少分配等待，但后续排队与 RX/USB 节奏未改善，暂不作为默认修复。
GATT DONE 在本机集成控制器路径可随 buffer 释放、交付 controller 时触发，不能视为无线发完。
完整对比、限制和后续线索见 [ATT3/ATT8 实测结论](22-att3-att8-results.md)。

## 定位目标与本轮范围

前两轮 1600/800 CPI 日志都显示 PMW 报告比 RX/USB 均匀，通知 API 调用最长 32–36ms，
但没有队列满、SPI 或 USB 错误。证据指向生成报告后、USB 前的链路节奏，不能据此断言
蓝牙硬件损坏、无线丢包、ATT 缓冲一定不足或光学安装完全正确。
本轮保持 800 CPI、8ms 最小报告间隔、顺时针 15°、原按键与 GPIO、配对数据。
不改 Dongle、BLE 连接间隔/latency、PHY、ACL/connection TX 配额或原协议。
两版共有的探针增加了执行开销；外设通知线程栈统一由 756 提至 1536B，为嵌套探针留余量。

| 右侧文件（本地 build/） | ATT TX 数量 | 用途 |
|---|---:|---|
| `prospector-right-bttrace-cpi800-att3.uf2` | 3，原值 | 先采基线，区分分配等待与提交后完成 |
| `prospector-right-bttrace-cpi800-att8.uf2` | 8 | 单变量对照，观察减少分配等待是否真正改善 RX/USB |

原 `prospector-right-pipeline-8ms-angle15-cpi800-cadence.uf2` 保留，可回退。
Dongle 使用已有 `prospector-dongle-pipeline-q64-cadence.uf2`，SHA-256
`8a857e1d02c95104f95f7cb539725630095967db64d53758d9accba160715be6`。
**只刷右键盘，左侧和 Dongle 本轮不刷。** 两版均为诊断候选，实机未验收，不宣称优化成功。

## 探针含义

沿用 PMW/TX/RX/USB 四个 CAD 阶段；新增右侧 `CAD stage=DONE`，仅完整 sync 帧
在本地 GATT 完成回调时计数。`bt_gatt_notify` 原本也调用 `bt_gatt_notify_cb`；本轮给同一路径
附加回调，保留 payload、广播订阅目标、超时和原返回值。

右侧每 2 秒新增以下汇总，绝不逐包打印或记录键位/键入内容：

| 日志 | 时段 |
|---|---|
| `BTT stage=CALL` | 通知 API 入口至返回 |
| `BTT stage=ALLOC` | ATT 调用的 `bt_l2cap_create_pdu_timeout` 分配路径 |
| `BTT stage=SEND` | `bt_att_send` 提交函数调用本身 |
| `BTT stage=FLIGHT` | `bt_att_send` 入口至本地完成回调，包括后续排队/调度 |
| `BTT stage=TOTAL` | 通知 API 入口至本地完成回调，包括分配 |

每项有 n、avg_us、max_us，及 <100µs、100µs–1ms、1–6、6–10、10–20、20–30、30–50、
>=50ms 八个时长桶。这里测的是墙钟耗时，包含线程可能被抢占的时间。
`ALLOC` 是真实分配调用耗时，仍不能等同于内核挂起的纯等待时间。
`FLIGHT` 名称不代表测得精确空口时间；完成回调不是 Dongle 应用处理完、更不是电脑收到的确认。

`BTSTAT att=3/8` 可以从日志识别实际候选。attempt/accepted/err/done 为通知数，
**不是完整 XY 帧数**；X、Y 通常分别通知。live/peak 是尚未释放的诊断记录槽数；
no_submit 为 API 返回成功但未走到 ATT 提交；early 为完成回调早于 API 返回，允许发生。
accepted 与 done 会跨两秒窗口，不要求逐窗口相等。

使用 32 个静态记录槽，回调前后均可重入计时，只有 API 返回与完成回调均结束才回收。
断连时不能安全假设回调已全完成，不抢先回收/复用槽；若耗尽则普通发送，skip 增加，
不为了测量丢弃输入。skip 非零时 DONE/ALLOC/SEND 等统计覆盖不完整，需标记而非认定无线丢包。
先重新上电右侧再开始一轮，避免前次断连残留；不用清除 BLE 配对。

通过链接器 wrap 外部函数，不修改 West Zephyr checkout、不复制整个内核。
只支持干净的固定 Zephyr `10ba6d0cb38bc3d258775d27982f707599320085`，单连接、无 EATT/多通知。
构建后反汇编必须证明 ATT 分配与 GATT 提交实际调用探针，否则脚本失败、不得交付。

## 刷写顺序

先令 **右键盘** 双击 Reset 进入 NICENANO，确保不是 Dongle 的磁盘：

```bash
cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-right-bttrace-cpi800-att3.uf2' /Volumes/NICENANO/
```

右侧和 Dongle 都通过 USB **数据线连接电脑**；键盘仍经 BLE 向 Dongle 发事件，右侧 USB 用于日志。
保持 macOS 速度、球的安装高度、两板摆放和 USB 连接方式不变。不要在 A/B 之间调整光学高度。
本轮不用 Razer/触控板做对照，不测试鼠标点击/拖拽。

## 确认串口

先关闭旧 `screen` 和采集器。只接 Dongle 时执行：

```bash
ls /dev/cu.usbmodem*
```

记录 Dongle 端口，再插入右侧数据线并重复，新出现的端口为右侧。
**下列命令沿用上次已识别的 Dongle 21201、右侧 21101；如本次不同，请替换 --port。**
插好后等约 15 秒，再开两个终端，不在采集中 Reset 或拔插。

终端 A（Dongle）：

```bash
python3 '/Users/paul/Workspace/Lab/prospector-pro/firmware/docs/prospector-touch/scripts/capture-right-profile.py' \
  --port /dev/cu.usbmodem21201 \
  --output "/Users/paul/Workspace/Lab/prospector-pro/firmware/build/reports/dongle-bttrace-att3-$(date +%Y%m%d-%H%M%S).log" \
  --seconds 150
```

终端 B（右侧）：

```bash
python3 '/Users/paul/Workspace/Lab/prospector-pro/firmware/docs/prospector-touch/scripts/capture-right-profile.py' \
  --port /dev/cu.usbmodem21101 \
  --output "/Users/paul/Workspace/Lab/prospector-pro/firmware/build/reports/right-800-bttrace-att3-$(date +%Y%m%d-%H%M%S).log" \
  --seconds 150
```

采集器名称含 right，但可用于两端。右侧应看到 `BTSTAT att=3`、`BTT stage=ALLOC`、
`CAD stage=DONE`；Dongle 应看到 `CAD stage=RX/USB`，不应看到右侧的 BTT。
启动残留/缓存可能出现，保留原日志；不要因开头旧字样就断定采集中重启。
若 15 秒无任何设备输出，先核对端口、数据线与候选，不用空文件推断无故障。

## 两版完全相同的动作

两端开始输出后启动计时，在纯文本编辑器空白文档进行键盘测试：

| 时间 | 动作 |
|---|---|
| 0–10s | 球静止、不打字 |
| 10–40s | 尽量连续、均匀中速滚球；避免频繁换指 |
| 40–70s | 慢速精细移动，复现颗粒感 |
| 70–90s | 球静止，快速重复按键；观察延迟/缺字 |
| 90–110s | 同时滚球与按键，观察两者是否互相影响 |
| 110–120s | 停止操作 |

等两个采集器 **150 秒自动结束**，不要提前 Ctrl-C。记录不可避免的停手、断连/重启，以及
中速/慢速、纯按键、同时操作的体感。分布包含真实停手，长间隔不能全部视为异常。

完成 ATT3 后刷 **右侧** ATT8：

```bash
cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-right-bttrace-cpi800-att8.uf2' /Volumes/NICENANO/
```

重新核对串口后重复以上两条采集命令，将两个 `--output` 文件名中的 `att3` 改为 `att8`。
看到 `BTSTAT att=8` 才按 ATT8 分组；其余条件/动作一致。最终发回四个日志和两版体感。
如果 ATT3 已出现重启、持续输入失效，先回退并发其两份日志，不继续扩大测试。

## 如何根据结果决定修复

| 观察 | 解释与下一步 |
|---|---|
| ALLOC 占据 CALL 主要长耗时；ATT8 使 RX/USB 间隔和体感同时改善 | 支持 ATT 资源压力方向；做打字/重连/长时回归后再考虑默认值 |
| ATT8 只缩短 ALLOC，却使 FLIGHT/live 增加，RX/USB 不改善 | 只是允许积压更多，不能当作修复；回到 ATT3，查控制器/完成与接收调度 |
| ALLOC 很短，FLIGHT 与 DONE 已明显成团 | 调查控制器发送、无线重传和完成回调调度；下一轮再测中央参数/射频摆放 |
| DONE 较均匀，RX 成团 | 优先查中央接收路径；完成回调并非准确空口时间，不能单凭两板异步时钟断言位置 |
| PMW 本身出现长空档/质量退化 | 重新结合真实停手、IRQ/光学高度调查，不能只调蓝牙 |

研究的其他方案暂不混入这次 A/B：

- **连接 latency=0**：当前 7.5ms/30 由 pinned ZMK central.c 的连接创建参数指定，
  不是只改右侧就能生效。需另做 Dongle 候选、查看实际协商参数，并评估电池代价。
  latency=30 不是每次运动都固定延迟 225ms。
- **PHY 2M / 更大 ACL 包**：两端能力、实际协商与射频条件都要核对；小包不保证受益。
  不直接套用面向电脑 BLE HID 的参数到这条 split BLE 链路。
- **X/Y 合帧**：当前按轴通知会增加通知次数，合并可减少传输开销，但改动两端协议与同步语义，
  必须保留相对位移和键盘事件可靠性。本次不改变协议。
- **键盘与指针发送公平性**：同一个 service 工作队列里持续排空指针可能影响按键，需结合
  同时操作日志和排队证据做有界批处理，不能靠盲目提优先级解决。
- **射频对照**：固定固件后，再单独比较距离/USB 延长线/避开金属与干扰源；本次保持摆放。

参考以本地固定源码为准：Zephyr gatt.h 的 notify_cb 语义、att.c 的分配超时与完成回调路径；
在线 [GATT API](https://docs.zephyrproject.org/latest/doxygen/html/group__bt__gatt__server.html)
仅作概念参考，较新文档的线程上下文描述不替代固定 4.1 源码。

## 复现

```bash
PROSPECTOR_PIPE_TARGET=right PROSPECTOR_POINT_CPI=800 PROSPECTOR_PIPE_CADENCE=true PROSPECTOR_BT_TRACE=true PROSPECTOR_ATT_TX_COUNT=3 bash firmware/docs/prospector-touch/scripts/build-pipeline.sh
PROSPECTOR_PIPE_TARGET=right PROSPECTOR_POINT_CPI=800 PROSPECTOR_PIPE_CADENCE=true PROSPECTOR_BT_TRACE=true PROSPECTOR_ATT_TX_COUNT=8 bash firmware/docs/prospector-touch/scripts/build-pipeline.sh
```

本地 native 使用真实 trace C 验证回调先返回/后返回、无订阅、分配/提交错误、线程隔离、
记录槽耗尽继续发送、跨报告窗口存活、时间回绕与所有时长桶。
新探针保持默认关闭。内核/驱动 checkout 不改写，老 UF2 不覆盖。构建与校验清单见 T5-07 release。

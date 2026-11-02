# T5-07 实机日志：ATT3 / ATT8 对照结论

2026-11-01：用户已完成两版采集。反馈 ATT8 似乎略好，但区别不明显。
本轮只分析既有日志与固定源码，没有生成新 UF2、修改运行时配置或刷写。

## 结论

**ATT8 暂不作为默认修复，保留实验候选，后续以 ATT3 为对照基线。**
ATT8 确实减少 ATT 分配阻塞与本地提交抖动，但延后阶段的等待增加，DONE/RX/USB 间隔
没有改善。主要可见问题已位于 ATT 提交后的本地 host/controller 队列与传输/接收路径，
尚未证明具体是空口重传、连接调度、HCI credit 或中央扫描造成。

## 原始证据与解析

四份原件保留在 `firmware/build/reports/`，不改写。逐条派生数据为同名 `.analysis.json`；
汇总在 `bttrace-att3-att8-comparison.analysis.json`，可用同目录 `analyze-bttrace-att3-att8.py` 复算。

- `dongle-bttrace-att3-20261101-183023.log`
  SHA-256 `599ace40afe83636d3d84fa7a1e97e88550991172c3ce6f07a95aca83dbd406a`；# capture_end bytes=58216 elapsed_s=122.6 reason=interrupted。
- `right-800-bttrace-att3-20261101-183025.log`
  SHA-256 `2756b04bc54fd9b819d048344d4b250902e2e323176c34ae4a6dab17c49867af`；# capture_end bytes=163931 elapsed_s=122.8 reason=interrupted。
- `dongle-bttrace-att8-20261101-183431.log`
  SHA-256 `8a718ca0b157fbbfe896ad2e88828f12fbbb033845aeb2119524e95413ef3f6b`；# capture_end bytes=54069 elapsed_s=110.9 reason=interrupted。
- `right-800-bttrace-att8-20261101-183432.log`
  SHA-256 `688b99aab046125675299b844e1579f2ad4ea392d85113a3462ff663ad8b713c`；# capture_end bytes=149632 elapsed_s=112.4 reason=interrupted。

四份采集均在 150s 前中止，约 111–123s，仍有充分运动与按键样本，无需仅为凑时长重采。
文件包含开机/前次串口缓存及 uptime 跳跃；没有把这些直接解释为采集中重启。
去除 ANSI，将串接的时间戳拆分，仅汇总完整字段/完整八桶的行，按时间戳+正文去重。
被排除的不完整行：右 ATT3 RX 1 行；Dongle ATT8 RX 1 行；右 ATT8 STATE/USB 各 1 行。
CAD/BTT 统计行没有不完整记录。两板时钟未同步，不按相同 uptime 对齐或虚构端到端延迟。

## 计时结果（按通知，不是按完整 XY 帧）

窗口均值已取整；以下按各窗口 n 加权，均值有小于 1µs 的舍入误差。
ATT3 共 12065 次通知；ATT8 共 13747 次。两轮动作、时长和按键占比不同，不是严格相同负载，
因此不把几毫秒差异直接认定为确定的因果性退化。方向在去除按键的活动子集仍一致。

| 指标 | ATT3 | ATT8 |
|---|---:|---:|
| ALLOC 平均 | 0.771ms | 0.036ms |
| ALLOC >=10ms 比例 | 3.64% | 0.022% |
| CALL 平均 | 0.989ms | 0.248ms |
| SEND 平均 | 0.124ms | 0.120ms |
| FLIGHT 平均 | 3.911ms | 6.039ms |
| TOTAL 平均 | 4.763ms | 6.152ms |
| TOTAL 最大 | 51.147ms | 78.582ms |
| 诊断槽 peak（含正在调用的通知） | 4 | 9 |

ATT8 并未消灭所有分配长尾，两轮 ALLOC 最大均约 36.7ms；但 >=10ms 频率从 439/12065
降至 3/13747。它减轻上游等待，却让更多通知进入后续队列。不能只凭 API 更快就认为鼠标更顺滑。

## 完整 sync 报告的节奏

| 阶段 | ATT3 6–10ms | ATT8 6–10ms | ATT3 30–50ms | ATT8 30–50ms |
|---|---:|---:|---:|---:|
| PMW 成功入 input | 89.23% | 87.92% | 0.30% | 0.74% |
| TX 本地 API 接受 | 64.26% | 86.93% | 1.17% | 0.75% |
| DONE 本地完成回调 | 45.53% | 43.16% | 8.40% | 9.38% |
| Dongle RX | 31.29% | 29.18% | 9.24% | 9.72% |
| USB 成功提交 | 31.40% | 29.13% | 9.24% | 9.72% |

ATT3 PMW/TX/DONE 各 6322 帧，包含 3 个开机唤醒零位移 sync；RX/USB 各 6319。
ATT8 五阶段各 7169 帧。间隔计数是否比帧数少一取决于探针先前历史，不强求各端相同。
计数相符不等于证明所有物理动作/按键都被扫描，或主机应用逐帧无丢失。
>=50ms 和最大帧间隔包含真实停手、开机/跨采集空闲，不作“最坏输入延迟”解释。

只取各阶段每两秒 >=180 帧的活动窗口，RX 的 30–50ms 占比仍为 ATT3 9.45%、ATT8 9.74%；
对应 PMW 仅 0.28% / 0.56%。这是各阶段活动子集，不逐窗口对齐，但足以说明现象并非仅由停手产生。

为减小按键负载差异，再取右端 key=0 且 attempt>=300 的两秒窗口：
ATT3/ATT8 ALLOC 均值 0.779/0.039ms，FLIGHT 4.033/6.203ms，TOTAL 4.890/6.317ms，
趋势一致。该筛选是日志活动子集，不宣称已精确分离用户动作表中的各阶段。

## 错误、排队、按键与传感器

- 两轮 SPI/input 错误、右侧队列满、notify 返回错误、分配/提交失败、诊断 skip 均为 0。
- 两轮 Dongle drop/handle_err、USB err/sem_timeout/mouse_err 均为 0；队列高水位均为 1。
- 中央排队 age 最大均 213µs；USB mouse_send 最大分别 1159/1190µs。
- 中央单事件处理峰值 ATT3 11.169ms、ATT8 4.150ms，不能宣称中央绝无抖动；
  但主要长间隔已见于入队前 RX，而且未积压，现有证据不支持 USB/中央事件队列是主要来源。
- 右键位通知 ATT3 496、ATT8 428，与中央/USB 各自计数匹配；没有这两个测量点之间的计数缺口。
  不等同于物理按键扫描或应用层无漏字的验收。
- RAW 样本 13032/14840，SQUAL 范围 128–157 / 128–158，sq0 均为 0；
  已取样的光学质量未显示崩溃，但不能覆盖无采样时段或证明镜片距离正确。
- 实际连接均为 7.5ms / latency 30，右端 STATE 均为 8ms / 15°，BTSTAT att=3/8 分组正确。

## 重要语义补充：DONE 不能视为无线发送完成

进一步沿 pinned Zephyr 源码核对：`att.c:245` 的 `att_tx_destroy` 在原始 ATT buffer
被释放时触发 GATT 完成回调；`hci_driver.c:800–832` 的集成控制器发送路径在
`hci_acl_handle` 成功后立即 `net_buf_unref`。`hci.c:5840` 的 `hci_acl_handle` 复制数据到
controller node 并 `ll_tx_mem_enqueue`，此时还不等于 RF 发完/对端收到。
`conn.c` 的 fragment view 被销毁时会释放父 buffer，因而本机配置可较早触发 ATT 回调。
这与两轮 early=7362/8132、许多 FLIGHT<100µs 相符。不是发现“负的空口延迟”。
因此更准确的读法是 **ATT 本地 buffer 生命周期/完成回调**；本地完成探针仍能定位队列转移，
但不能据此判定无线已发出、无重传，或单独把 DONE→RX 差异全归到中央。
之前文档已说明不是精确空口/应用 ACK；本次明确补充其可能在交付 controller 时触发。

## 下一步优先级（未实现/未实测）

1. 测 HCI Number Of Completed Packets 及 controller 提交/credits，而非再次增加 ATT 队列。
   `host/hci_core.c:561` 此事件归还 controller packet credit，并移除 tx_pending。
   事件可能批量上报、包含其他 ACL 流量，仍不是主机应用收到的逐帧 ACK；需正确区分。
2. 调查 Dongle 在缺少另一侧时的后台扫描。当前有效配置 CENTRAL_PERIPHERALS=2，
   四日志每窗口仅见一个 split 连接；pinned `central.c:885–918` 在存在空槽时启动
   `BT_LE_SCAN_PASSIVE`，连接后会再次调用 start_scanning。该宏是 60ms interval/30ms window。
   扫描与已建立连接共享射频，是值得优先做单变量对照的具体线索；本次没有 SCAN 状态计数，
   **尚不能证明扫描实际持续运行或就是约 45ms 空档的根因**。不把 PERIPHERALS 盲目改成 1，
   以免限制将来双侧连接或影响当前绑定槽/UI。应独立测量扫描状态和受控策略。
3. 若控制器/扫描证据仍不足，再做 latency=0 的 Dongle 单变量候选，检查协商结果与电池代价。
   同轮不改扫描、latency、PHY、多个缓冲配额。
4. XY 合帧、按键/指针队列公平性是后续协议/调度方向，需更多证据与两侧兼容验证。

本轮不要求用户重采同一固件。ATT8 文件不删除、不合入生产默认；新一轮对照建议以 ATT3 为基线。
用户若当前停留 ATT8，不需为本次分析立即反复刷写。

## T5-08 诊断已实现（实机待验）

后续实现 HCI 完成统计与同一 Dongle 固件中的有界扫描 ABBA，保持 800 CPI / ATT3。
不需要为扫描开/关重复刷两份 Dongle；双端一次采集约 95 秒，原始证据自动打包。
见 [快速操作与决策标准](23-hci-and-scan-ab.md)。

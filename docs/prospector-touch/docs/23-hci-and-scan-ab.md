# T5-08：一次采集完成 HCI 与扫描 ABBA 对照

**实测更新：** 已取得有效95秒ZIP，后台扫描是当前单侧在线周期性长空档的主要来源。
不需要重做同一测试；[四阶段数据与下一步修复](24-scan-ab-results-and-fix.md)。

## 本轮要回答什么

保持右侧 800 CPI / ATT3 / 8ms / 顺时针 15°；先前 ATT8 仅转移了等待，没有明显改善 RX/USB。
本轮增加真实 controller ACL 提交与 HCI Number Of Completed Packets 事件探针，
同时在同一 Dongle 固件、同一连接中按 ON/OFF/OFF/ON 切换后台扫描，单一行为变量是扫描。
不改连接 interval=7.5ms / latency=30、PHY、键位、GPIO、配对数据或两个外设槽的配置。
本地构建/模拟/UF2 检查通过不代表实机已改善；实际效果待用户验收。

## 缩短测试流程

- 各刷一次右侧和 Dongle，不再为开/关扫描反复刷两个 Dongle 文件。
- 一条 Python 命令并行捕获两端，自动提示四段动作、确认切换、恢复正常扫描。
- 四段各 20 秒，动作共 80 秒；总采集约 95 秒，自动结束。
- 自动计算 Dongle RX/USB 开关对比，HCI 分配到保守的宿主接收时间窗口，保存原件并打包 ZIP。
- 下一轮只需提供一个 ZIP 和四段体感，不重复采集无信息增益的 CPI/ATT 参数组合。

## 刷哪两个固件

1. **右键盘** 双击 Reset 进入 NICENANO，只复制：

```bash
cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-right-hci-cpi800-att3.uf2' /Volumes/NICENANO/
```

2. **Dongle** 从已验证的设备页双重确认进入 NICENANO，只复制：

```bash
cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-dongle-scan-ab.uf2' /Volumes/NICENANO/
```

每次只让目标板进入 NICENANO，避免刷错。左侧不更新，本轮保持关闭；未组装则不用处理。
两板均用 USB **数据线连电脑**，右侧 USB 用于日志，输入仍通过 BLE 到 Dongle。
右侧新探针只增加 HCI_TRACE=y；设备树和实际驱动与 T5-07 ATT3 相同。
Dongle 增加 SCAN_AB=y 和 T5-08-RADIO 标识；设备树不变。保留原回退 UF2。

## 一条采集命令

关闭旧 screen/采集器，接好两端后等约 15 秒。端口沿用此前识别：Dongle 21201、右侧 21101。
若端口变化，先只接 Dongle 执行 `ls /dev/cu.usbmodem*`，再接右侧，新增项是右侧；替换下方参数。

```bash
python3 '/Users/paul/Workspace/Lab/prospector-pro/firmware/docs/prospector-touch/scripts/capture-radio-ab.py' \
  --dongle-port /dev/cu.usbmodem21201 \
  --right-port /dev/cu.usbmodem21101
```

无需 pip 依赖，无需两个终端。不要在采集中 Reset、拔插、改变安装高度/主机速度或移动其他鼠标。
保持屏幕布局、设备距离和供电方式相同。这轮只滚球，不增加点击、拖拽或打字阶段。

| 段 | 扫描 | 动作 |
|---|---|---|
| 1 | 开 | 按提示中速 10 秒，再慢速精细移动 10 秒 |
| 2 | 关 | 同样动作 |
| 3 | 关 | 同样动作 |
| 4 | 开 | 同样动作 |

开头约 5 秒先静止。脚本只显示阶段提示与摘要，完整串口内容另存。
看到“对照完成”后停手，继续等待自动保存结束。提示中的开关必须来自固件确认，不靠主机计时猜测。
如果要中止，Ctrl-C 会通知 Dongle 恢复正常扫描；即使采集器掉线，固件也会在约 80 秒内结束。
如果连接数量变为 0 或 2、扫描 API 失败、缺少新版右侧 HCI 或设备确认，脚本报错并保存证据，
不把失败测试当作有效 A/B。如果恢复确认失败，请保留日志并重启 Dongle。

完成后输出形如：

`firmware/build/reports/radio-ab-YYYYMMDD-HHMMSS.zip`

ZIP 包含 dongle.log、right.log、host-events.jsonl、summary.json；发回这个 ZIP 即可。
补充体感：2/3 段是否比 1/4 段更顺滑；停手或异常发生在哪一段。

## 探针与安全边界

### HCI（右侧）

- `__wrap_hci_acl_handle` 在原 controller ACL 提交之前记录时间，原调用、buffer、返回值保留。
- `__wrap_hci_num_cmplt_encode` 在集成控制器生成 Number Of Completed Packets 事件时统计。
  两个外部调用都须通过最终 ELF 反汇编证明实际经过 wrapper。
- 16 个静态槽，按连接 handle FIFO 匹配，给出 tx/events/completed/matched/pending/peak/batch，
  以及匹配完成年龄的平均、最大和八桶；全部 ACL PDU 都计入，不只是鼠标或 sync。
- `CAD stage=HCI_EVT` 是完成**事件**间隔；一次事件可完成多个包，不能与鼠标帧数直接比较。
- orphan/overflow/reset/err 非零时标记统计缺口；不改包流来挽救测量，不丢弃真实输入。
- 断连清除计时匹配状态；时间/序号回绕、提前完成、失败与满槽均有真实 C 的模拟覆盖。
- 完成事件比之前 GATT buffer 释放更接近 controller 实际完成，但仍包含 controller 通知批处理/调度，
  不等于精确空口时间，更不是电脑应用确认。没有射频抓包就不宣称测得重传次数。

### 扫描（Dongle）

- 普通启动保持原扫描行为；只有收到本轮 `!P8 START <run>` 命令才开始有界实验。
- 只在恰好一个 split 外设连接时开始；连接保持，OFF 只调用扫描停止 API，并阻止缺侧扫描重启。
- 完成、STOP 或连接数量变化后解除阻止并调用原 start_scanning，恢复**原有正常策略**。
  不改 PERIPHERALS=2、不修改绑定、不主动请求断开任一现有连接。
- scan 值是由 ZMK 状态与 API 成功结果确认的逻辑状态，不是外部射频嗅探结果。
- nonce run 区分新测试和 USB 缓存。超长/无效命令不执行，STOP 必须匹配当前 run。
- 新扫描控制只编入诊断候选，默认关闭，不作为生产设置持久化。

### 统计窗口

summary.json 只用完整董端两秒窗口，排除切换后 2 秒和结束前 1 秒。仍包含真实停手，
长帧间隔不是必然卡顿；两段 ON、两段 OFF 的趋势需分别一致才有说服力。
右侧 HCI 用 host-events 的接收时间做保守归属，排除开始 3 秒/结束 2 秒，
USB 缓存/调度仍可影响归属，不能当作同步设备时钟或逐帧端到端映射。
HCI 均值按 matched 数加权；hci_measurement_clean 要求两种模式都有样本且选中窗口无匹配异常。
自动摘要只显示数字，不自行宣称已修复或确定根因。

## 明确的去留标准

- **OFF 两段 RX/USB 的长间隔和体感都明显改善，ON 恢复出现：** 优先做缺侧扫描降占空比/
  有界搜索策略修复，并保留新键盘发现和断线重连。修复后再统一做按键、双侧与重连回归。
- **扫描切换有效但没有改善：** 不保留永久关闭扫描；根据 HCI 完成年龄/批量/事件节奏，
  再做一个保持其他项不变的 latency=0 或控制器发送额度对照，不重复测试 ATT8。
- **RX/USB 已平滑但慢速仍颗粒：** 重新分离光学高度/源端量化与主机处理，而不是继续扩队列。
- **阶段失败或样本不足：** 只重做失败部分/修正采集问题，不把空日志或中断日志当通过。

## 构建复现与记录

```bash
PROSPECTOR_PIPE_TARGET=right PROSPECTOR_POINT_CPI=800 PROSPECTOR_PIPE_CADENCE=true PROSPECTOR_BT_TRACE=true PROSPECTOR_ATT_TX_COUNT=3 PROSPECTOR_RADIO_AB=true bash firmware/docs/prospector-touch/scripts/build-pipeline.sh
PROSPECTOR_PIPE_TARGET=dongle PROSPECTOR_PIPE_QUEUE=64 PROSPECTOR_PIPE_CADENCE=true PROSPECTOR_RADIO_AB=true bash firmware/docs/prospector-touch/scripts/build-pipeline.sh
```

构建资源、哈希、原文件回退与 native/实际链接证据见 `releases/T5-08/`。
本轮没有自动给设备刷写或运行物理对照；模拟测试的数字不是实机改善结果。

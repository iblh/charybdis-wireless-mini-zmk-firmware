# Prospector Pro — Project Handoff / 本地开发交接包

**2026-11-12 当前基线：** 用户确认T5-12已刷入、没有问题、左右均能连接。
当前二进制冻结为v0.1.0-rc1候选包，保留原版本和SHA，不要求因整理重刷。
[候选包与验收边界](releases/v0.1.0-rc1/README.md)

**2026-11-10 T5-12 本地候选：** 系统/亮度页改版、共享亮度面板、USB-only Studio。
64KB/32位 LVGL 和单目标构建验证见 [新页面、再次换左主控、USB查看键位](docs/31-controls-usb-studio.md)。
新主控双侧连接已通过；USB RPC、KeyPeek与完整新版回归单独验收；右侧800 CPI/ATT3/8ms及r2扫描策略保留。

**T5-11 已有实机反馈：** 用户确认 LEFT CLEARED、K1/K2 都 ON，原右侧与第一次更换的裸左侧已连接。
这不代表完整左侧矩阵或双侧打字验收。2026-11-10 用户确认之后又换了另一块左主控，
必须使用新的 v2 一次性维护事务，不能重复使用 v1 或清全部绑定。
见 [首次维护记录](docs/30-left-slot-recovery.md) 和上方 T5-12 步骤。

**2026-11-01 T5-09B 当前基线：** 用户确认T5-09屏幕正常但键盘无法连接，回退T5-08恢复。
已定位生成central改变链接顺序，导致其Settings回调在BLE初始化时丢失；新版显式固定50/51/52顺序。
本地Build、启动故障复现/修复、实际ELF顺序与UF2检查通过；用户已确认右侧自动连接、断电重连正常，轨迹球控制明显改善。
只刷Dongle的 `prospector-dongle-scan-policy-r2.uf2`；右侧不变，不清除配对。
详见 [启动顺序修复与最短验收](docs/26-scan-startup-regression.md)；旧T5-09已标记有回归。
双侧与长时间稳定性仍待验收；[当前优化结果和后续任务](docs/27-current-baseline-and-next-steps.md)。

**2026-11-01 T5-08 实测定位：** ON/OFF/OFF/ON 四段有效，扫描开启时 RX 的30–50ms间隔
两段约9.5%，关闭后约0.4–0.5%，重新开启复现；HCI ≥30ms 长尾同步消退，源端PMW基本稳定。
用户确认关扫描有改善、仍有颗粒感。后台扫描是当前单侧在线周期性卡顿主因的强证据。
已据此生成Dongle缺侧扫描策略候选（见上方最新记录），保留自动发现/重连，未宣称全部问题解决。
详见 [逐阶段结果与修复方案](docs/24-scan-ab-results-and-fix.md)。

**2026-11-01 T5-08：** 右侧保持 800 CPI／ATT3，新增 controller ACL 提交和 HCI 完成事件计时；
Dongle 以同一固件有界切换扫描 ON/OFF/OFF/ON，不改连接参数。两个候选均本地构建/测试/
实际链接与 UF2 检查通过，实机待验。各刷一次，一条命令采集约 95 秒，输出一个 ZIP。
具体操作与明确去留标准见 [HCI 与扫描快速对照](docs/23-hci-and-scan-ab.md)。

**2026-11-01 ATT3/ATT8 实测：** ATT8 将 ALLOC 均值从 0.771ms 降至 0.036ms，但本地回调
TOTAL 从 4.763ms 到 6.152ms，RX 30–50ms 比例 9.24% / 9.72%，USB 跟随，未显示整体改善。
用户体感区别不明显；暂不作为默认修复，保留实验版本。DONE 在本机可能只是 buffer 交付控制器，
下一步需 HCI completion/credits 与中央缺侧扫描状态。详见 [完整分析](docs/22-att3-att8-results.md)。

**2026-11-01 T5-07：** 新增真实 ATT 分配/提交耗时和本地完成回调探针，保持 800 CPI。
ATT3 基线与 ATT8 单变量对照已本地构建、native、实际机器码与 UF2 限额检查通过，实机待验。
只刷右侧，Dongle 不变；两版共同扩展 service 栈，配对/键位/采样与连接参数不改。
刷写和双端日志采集见 [T5-07 操作步骤](docs/21-ble-buffer-and-completion.md)；未宣称卡顿已修复。

**2026-11-01 01:39 复测：** 日志确认已运行 800 CPI（文件名仍含 1600）；PMW/TX/RX/USB
6–10ms 占比约 91.0/65.7/32.3/32.5%，无 SPI/队列/USB 错误，通知调用最长 36.285ms。
源码确认独立线程有等待 ATT 缓冲的路径，尚待分段测量证明实际耗时来源。
用户报告球到镜片约 3mm；须按镜片基准面核对 2.2–2.6mm 工作距离。
详见 [最新分析](docs/20-upstream-cadence-investigation.md)；本轮未改运行时固件，卡顿未标记解决。

**2026-11-01 01:26 日志更新：** 四阶段各 5093 帧，6–10ms 间隔占比从 PMW 92.85%、
TX 67.43% 降至 RX 33.01%，USB 33.26%；本次无 SPI/队列/USB 错误。
右侧通知调用最长 32.409ms（包含可能抢占，非空口时延）。优先调查 BT 提交与无线/接收调度。
用户要求回到 800 CPI，已提供只改 CPI 的 T5-06 右侧版本，本地通过、实机待验；Dongle 不变。
详见 [最新四阶段结论与 800 版](docs/20-upstream-cadence-investigation.md)。

**截至：2026-10-23 | Status: ZMK firmware compiled & display boots on actual device.**

**2026-11-01 T5-06：** 用户已提供 cadence 双端日志。RX 与 USB 间隔分布近似，
均出现短间隔成团与频繁 30–50ms 间隔；中央无丢事件/USB 错误。
定位范围前移至右侧报告、发送/无线/接收调度；新增右侧 PMW/TX 两个探针候选，
保持当前 Dongle 不变，本地通过、实机待验。见 [数据与下一轮](docs/20-upstream-cadence-investigation.md)。

**2026-11-01 后续实测：** 用户确认 1600 CPI 并降低主机速度后，慢速颗粒感仍存在。
下一步启用已有 Dongle 帧间隔统计版，右侧/主机设置保持一致；网页 delta 图是事件位移幅值，
不能直接当作硬件报告频率。刷机、双端采集和动作表见 [帧间隔测试](docs/19-cadence-test-protocol.md)。

**2026-11-01 T5-05：** q64 双端测试中未见队列丢事件/USB 错误，用户反馈按键可用；
剩余感觉为慢速精细移动颗粒感。准备右侧 1600 CPI / 8ms / 15° 单变量对照，
Dongle 保持原 q64。另备帧间隔统计版，暂不要求同时刷写。
本地通过、实机待验，见 [分析与测试](docs/18-trackball-fine-motion.md)。

**2026-11-01：** 已取得右侧真实 8ms 串口日志：PMW 初始化成功，运动片段无可见 SPI/input
入队错误，IRQ 工作等待最大约 1ms；尚未覆盖 Dongle 接收/USB，不能据此排除下游卡顿。
用户暂缓鼠标按键测试，下一步选原键位 q64 Dongle，保持右侧 800 CPI / 8ms / 15°。
USB 高亮表示 Dongle 到电脑的输出通道，与键盘通过 BLE 接入不冲突。
详见 [日志结论与后续](docs/17-input-pipeline-debug.md)。

**2026-10-31 T5-04：** 用户反馈右侧 8ms 版仍有鼠标卡顿，快速打字也出现延迟/缺字。
新增双端链路诊断及中央队列 5/64 项对照，修正 WPM/输出控件跨线程访问；
另提供 15°/40° 方向对照，不宣称卡顿已修复。先只刷 Dongle 收集日志，
步骤、MAC-DV 鼠标操作与清理范围见 [输入链路诊断](docs/17-input-pipeline-debug.md)。
用户后续澄清目前仅组装右侧；增加独立 `RIGHT TEST` Dongle 候选，提供右侧 NAV 鼠标入口。
原空日志采集的是 Dongle，右侧当时只接充电器；电池实测 3.5V，与上报约 8% 相符。

**2026-10-31 最新：** 用户已基本组装完成，正常右侧固件下连续运动仍有轻微卡顿，
方向整体约逆时针偏 15°。T5-03 新增右侧顺时针 15° 校正、延迟采样时保留未报告
位移、低频光学/队列统计，提供 12ms/8ms 两个对照候选；本地检查通过，实机待验。
操作与现有点击/滚动键位见 [方向与性能诊断](docs/16-trackball-calibration-and-performance.md)。

**2026-10-30 最新：** 用户重新焊接第二块 PMW3610 + Breakout，已观察到鼠标运动；
当前为 LM18-LSI 装好后的手持测试，高度变化会丢失追踪。优先固定镜片、传感器
与球座并验证工作距离，尚未验收稳定性。第一块板复位低的根因未定。
见 [光学安装与验收](docs/15-trackball-optical-validation.md)。

**2026-10-24 更新：** 用户已确认三布局循环、下滑亮度、设备页及双重确认进入 NICENANO 正常。
T5-01 的 MAC-DV / WIN-DV / GAME 已实现并通过本地测试，尚待实机验收；真实键盘已到手，左右均为 nice!nano v2 兼容 nRF52840，
该日期时尚未刷入和配对（后续状态见 2026-10-27 更新）。最新候选固件、本地验证与实机待测状态见 `docs/06-roadmap-and-acceptance.md`；
键位、模式切换及首次配对见 `docs/11-input-modes-guide.md`。下面的“已验证 CI”及早期缺口为交接时历史记录。

**2026-10-27 更新：** 用户已刷入左右外设并通过 Dongle 打字，初步键位正确。
切换外观时显示状态不更新、左右指示器反向已定位并制作 T5-02 本地候选；
右侧 PMW3610 在电池/USB 供电均完全不动；用户日志确认产品 ID 读为 0xFF、初始化失败。
用户 PCB 制造文件与固件 GPIO 匹配；增加 1 秒等待的诊断版实测仍失败，
新测量 VDDIO=3.3V、NRESET≈0V，正优先排查复位上拉网络，尚未改焊或认定芯片损坏。
最新操作与测试见 [显示状态与轨迹球诊断](docs/14-peripheral-state-and-trackball.md)。

这是交接上下文和已有修改的**归档**，不是一个用于替换你当前两个 Git 仓库的完整源码副本。你 Mac 上的 `firmware/`、`module/` 两个 Git clone 是代码权威来源；本目录保存项目历史、技术决策、测试记录、源文件补丁快照、自动核验脚本和下一步开发说明。不要重新运行归档中的 `apply_patch.py` 去覆盖现有代码。

整理后的仓库边界、固定依赖和提交前检查见 [仓库整理记录](docs/13-repository-organization.md)。

## 阅读顺序 / Start here

1. `AGENTS.md` — 给 Codex / ChatGPT Work 的工作约定、现状和行为要求（建议放在 workspace 根目录）
2. `docs/01-project-brief.md` — 目标、范围、当前验收程度
3. `docs/02-hardware-pinout.md` — **现有验证过的 GPIO** 和 UF2 记录
4. `docs/03-repositories-and-build.md` — 两个 Fork、分支、成功 CI、构建步骤
5. `docs/04-history-and-evidence.md` — 从 Arduino 到 ZMK 的真实历史
6. `docs/05-code-architecture.md` — CMake / Kconfig / Devicetree / LVGL 入口
7. `docs/06-roadmap-and-acceptance.md` — 用户期望的一次到位版本、待实现及测试
8. `docs/07-troubleshooting.md` — 曾出现的错误及已知风险
9. `docs/08-decisions-and-open-questions.md` — 已定方案、不应该随意推翻的限制
10. `docs/09-agent-first-task.md` — 本地 Codex/Work 的第一批操作
11. `docs/10-touch-device-and-input-modes.md` — 新设备页、双重确认触屏刷机、MAC-DV / WIN-DV / GAME 完整实施方案（设计阶段）

## 仓库中的位置与工作区

此目录现正式纳入 firmware 仓库：`docs/prospector-touch/`。模块实现仍在独立的
[Prospector module 仓库](https://github.com/iblh/prospector-zmk-module/tree/feat/touch-no-sensor)。
历史记录的 SHA 和 CI 成功时间保持原样，不代表后续候选已获得实机验收。

推荐布局：

```text
prospector-pro/
  AGENTS.md
  firmware/                    # 固件配置、硬件、构建入口和本文档
    docs/prospector-touch/
  module/                      # UI、行为、驱动和主机测试
  prospector-pro-handoff -> firmware/docs/prospector-touch
```

现有工作区已保留 `prospector-pro-handoff` 兼容快捷路径，之前的命令仍可使用。
新 clone 可直接从工作区根目录运行正式路径：

```bash
bash firmware/docs/prospector-touch/scripts/verify-workspace.sh
PROSPECTOR_KEYMAP=touch_modes SKIP_WEST_UPDATE=true bash firmware/docs/prospector-touch/scripts/build-touch-only.sh
bash firmware/docs/prospector-touch/scripts/build-touch-peripherals.sh
```

首次构建需要 West 依赖时省略 `SKIP_WEST_UPDATE=true`。`module/` 必须使用
`firmware/config/west.yml` 记录的模块提交；本地构建会使用这个 sibling 工作副本。

Git 中保留源代码、构建/验证脚本、文档和原始成功 CI 证据；`firmware/build/`、
依赖 checkout、临时渲染缓存仍为本地文件。当前 UF2 的校验清单也保存在
[当前基线记录](releases/T5-09B/README.md)，候选状态与实机验收分别记录。

## 交接时历史记录：已有证据 vs 未经验证

- **已确认：** Arduino LCD SPI 显示成功；Touch I²C `0x15` ACK；GitHub Actions #39911723815 `success`；用户已刷入 `charybdis_dongle prospector_adapter-qwerty.uf2`，ZMK 屏幕**能点亮**。
- **尚未确认：** 点击 `SET` 的实际响应、触摸坐标与 IRQ、真实亮度 PWM（目前 LCD_BL 先前接 3.3V）、重启后亮度持久化、左右键盘 BLE 配对、触摸唤醒、四 UI 运行时切换、稳定性/功耗。
- **明确排除：** 环境光传感器/APDS9960；3D 外壳已打印，当前无需外壳设计/装配步骤。

## 已验证 CI 固件（包含真实 UF2）

- `artifacts/ci-39911723815-qwerty/`：从 GitHub 上 #39911723815 的真实成功产物下载，包含原始 ZIP、用户实际刷入并成功点亮屏幕的 Dongle UF2、两个尚未验证的左右键盘 UF2，以及 SHA-256 与 UF2 Header 记录。注意不要刷错目标。

## 源码与旧补丁

- `reference/verified-touch-files/`：交接时核对的 Touch `.conf` 和之前的实现源文件，仅用于 diff / 回溯，不是 source of truth。
- `archive/2026-10-21-original-touch-patch/`：最初生成的 `apply_patch.py` 等原始文件，包含编译错误修复**之前**的 `.conf`，只读归档。
- `archive/prospector_touch_implementation_pack_original.zip`：早期源码包原件。
- 两个最新 Git Fork 必须以各自分支为准，不能用这些旧文件整体覆盖。

## 一段可直接贴给 Codex / Work 的开场请求

> 请先阅读工作区根目录的 `AGENTS.md` 和 `prospector-pro-handoff/README.md`，再按 `docs/09-agent-first-task.md` 核对本地两个仓库、分支和修改状态。项目 ZMK 无光照传感器版本已编译成功并在设备上点亮，当前目标是在保留原功能的前提下完善触控、手动亮度、休眠/唤醒和运行时设置。先做准确的现状盘点和可执行改造计划，再编辑代码、尝试本地单目标编译。不得随意运行原始补丁覆盖已修改文件，不能假设键盘已配对或触控已验证。

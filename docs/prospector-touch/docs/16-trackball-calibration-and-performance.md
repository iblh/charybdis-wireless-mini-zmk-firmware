# T5-03：方向校准、连续卡顿诊断与鼠标操作

后续实测：8ms 的纵向大致正确、横向仍偏，快速打字也出现延迟/缺字。
T5-03 尚未验收稳定性；双端定位及新的对照固件见 [T5-04](17-input-pipeline-debug.md)。

## 实机反馈与当前结论（2026-10-31）

用户基本完成组装并安装键帽，右侧使用正常版
`prospector-touch-right-peripheral.uf2`，不是逐次输出 DEBUG 的旧诊断版。
前推球时指针向左偏约 15°，横向滚动轨迹约为左下到右上、偏 15–20°。
持续滚动时也有轻微卡顿，不仅是闲置后第一下。因此：

- 方向表现与整体逆时针约 15° 的坐标偏转一致，先试屏幕坐标顺时针 +15° 校正。
- 不能把当前卡顿归因于旧诊断日志；也不能仅凭主观卡顿认定 BLE 丢包。
- 现有 800 CPI、采样模式和 GPIO 保持原配置；正常外设报告节流为 12ms，理论
  上限约 83 次/秒。8ms 对照版的理论上限约 125 次/秒，实际取决于传感器事件、
  BLE、USB 与主机处理，不是已保证的端到端频率。

## 两个临时右侧候选

| 文件（位于 firmware/build） | 方向 | 最短报告间隔 | 用途 |
|---|---|---|---|
| `prospector-right-profile-12ms-angle15.uf2` | 顺时针 +15° | 12ms | 诊断基准 |
| `prospector-right-profile-8ms-angle15.uf2` | 同上 | 8ms | 仅改变报告间隔的对照 |

仅刷右侧，Dongle 和左侧保持当前固件，保留绑定。完整源清单/构建验证见
[T5-03](../releases/T5-03/README.md)。两份均为本地候选，方向和流畅度尚待实机验收。
两版都增加 1000ms 传感器上电等待、同一套统计、同一旋转；与用户当前正常版相比
有这些变化，以及下述共同的缓存保留修复，因此用两份新候选彼此比较，不能把
与旧版的任何差异只归因于报告频率。

方向使用预计算 Q20 正弦/余弦与 64 位整数运算，不在 MCU 上计算浮点三角函数。
保存小数余量，避免慢速小位移被逐帧截断；必须先消耗原驱动累加值，再做旋转，
防止旋转后暂时输出零的帧被重复累加。校正位于右侧驱动运动输出前，因此随后
Dongle 的普通指针、SLOW 和 SCROLL 都使用校正过的坐标。现有轴交换/反向保持。

另修正原驱动的一处位移丢失：原先在样本间隔达到报告周期时直接清空 dx/dy，
可能把上一次节流尚未发出的有效位移一起丢掉。两个候选都保留该缓存，下一次
报告机会继续输出；原有唤醒时主动清缓存/丢前三次 burst 的策略保持并单独计数。
native 测试用 4ms/24ms 的不规则样本间隔验证此修复。它是源码中的确切问题，
是否解释用户实机卡顿以及修复后体验改善程度仍待验收。

这是编译参数，尚无触屏运行时角度设置。先试 +15°；若仍偏，可按实际观察改成
其他角度重新构建，范围 -180° 至 +180°，正值为屏幕坐标顺时针。

## 源码安全与本地验证

权威新增实现放在 `firmware/local-build/trackball-profile/`。构建工具要求原始
PMW3610 checkout 是干净的固定提交 `f6e234367b22508b5c0a6bcc82437c64f320089b`，
仅在带生成标记的 `firmware/build/...-driver/` 副本中加入统计和旋转钩子。
`prepare_driver.py` 对每个源码替换位置做唯一性检查。West 原 checkout、依赖锁定、
正常外设配置和既有已发布 UF2 不被覆盖。模块名保持一致，使 staged driver 替换
manifest 的同名模块，避免两个驱动同时链接。

验证：

- 实际旋转 C：零度、正负 90°、正负输入、15° 校准、小数累计、方向反转、饱和无
  残留巨量位移。
- 从 staged driver 提取实际 `pmw3610_report_data()` 进行 native 测试：单计数慢动，
  等间隔 4ms 输入经过 12/8ms 报告节流，以及含 24ms 延迟的输入；最终总位移守恒、
  零输出帧不重复计数。
- 实际 profiler C：质量/快门统计、队列错误透传、IRQ 到 work 等待、定时状态与窗口清零。
- 串口采集器：伪终端端到端读取、跨读取 UTF-8、拒绝覆盖已有日志；未用真实设备测试。
- Docker/West 两个右侧单目标构建和 UF2 guard；最终 `.config` 的有效设置仅最短
  报告间隔不同（目录注释另有差异），展开后的 devicetree 相同。详细数值与哈希见 JSON。

没有自动刷写、没有清配对、没有改 GPIO。module 仓库无本轮改动。

## 日志含义与边界

每两秒汇总一组：

- `STATE`：ready、初始化步骤/错误、报告间隔和角度；即使错过开机日志，后续仍能看到状态。
- `RAW`：此窗口读取的运动 burst 数、非零样本数、旋转前的有符号/绝对位移、SQUAL
  最小/平均/最大和为零次数、快门范围。SQUAL 取现有 burst 第 4 个偏移，和当前
  Zephyr PMW3610 实现一致，不在统计线程并发发起额外 SPI 读取。
- `PIPE`：向 Zephyr input API 提交的轴事件数及返回错误、运动 burst SPI 错误、
  唤醒丢弃次数、最大样本间隔和 IRQ 等待 work 的最长毫秒数。
- `LINK`：实际连接间隔（微秒）、peripheral latency；不打印蓝牙地址。

`n=0` 可以只是没有滚动，不能把此时的零质量值解释为失焦。`gap_ms` 会包含正常
停顿，不是丢包统计。较低质量与异常运动的相关性需要在同样持续滚动条件下比较，
没有通用 SQUAL 通过阈值。`input_err=0` 也不能证明 BLE 或主机没有丢失事件。
这些统计主要覆盖传感器到右侧 input 提交点，不是端到端延迟测量。

## 用户测试步骤

1. 退出已有 screen：Ctrl+A → K → Y。右侧双击 Reset，确认 NICENANO 是右键盘。
2. 先刷 12ms 候选：

   ```bash
   cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-right-profile-12ms-angle15.uf2' /Volumes/NICENANO/
   ```

3. Dongle 保持接电脑；右侧额外接 USB 以供电/采日志，左侧保持原状。两版测试使用
   同一主机、相同 USB 位置和球座固定状态。右侧诊断 USB 只提供 CDC，不直接发 USB 键盘。
4. 找到右侧串口：`ls /dev/cu.usbmodem*`。以实际名称替换下面端口；不要同时运行 screen：

   ```bash
   python3 '/Users/paul/Workspace/Lab/prospector-pro/firmware/docs/prospector-touch/scripts/capture-right-profile.py' \
     --port /dev/cu.usbmodem21201 \
     --output '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/reports/right-profile-12ms-01.log' \
     --seconds 90
   ```

   端口号可能变化，不能默认一直是 21201。日志文件已存在时改用新尾号，脚本拒绝覆盖。
5. 前 10 秒不动；接着约 20 秒只反复前推，抬手回位，不把球往后滚，用来检查方向；
   再约 30 秒连续画圈/左右慢动；最后静置约 15 秒后重新滚动。记下卡顿出现的大致时刻。
   如 STATE 仍 `ready=0`，保存错误记录即可，不将无运动归因于报告频率。
6. 退出采集、右侧进入 NICENANO，刷 8ms：

   ```bash
   cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-right-profile-8ms-angle15.uf2' /Volumes/NICENANO/
   ```

   重复相同测试，输出文件改成 `right-profile-8ms-01.log`。8ms 若更卡，可立即回退 12ms
   或原正常右侧 `prospector-touch-right-peripheral.uf2`；不要通过清绑定修复表现差异。
7. 回传两份日志，以及 +15° 后前推/横移是否对齐、哪版更顺畅、是否仍持续卡顿。

通过后再去掉诊断开销制作正常版，并分别验证电池/USB、左右键输入、拖拽、滚动、
慢速与停放唤醒。当前候选都用 USB 采样，不代表电池供电已验收。

复现构建：

```bash
PROSPECTOR_POINT_INTERVAL_MS=12 PROSPECTOR_POINT_ANGLE_DEG=15 bash firmware/docs/prospector-touch/scripts/build-right-profile.sh
PROSPECTOR_POINT_INTERVAL_MS=8 PROSPECTOR_POINT_ANGLE_DEG=15 bash firmware/docs/prospector-touch/scripts/build-right-profile.sh
PYTHONDONTWRITEBYTECODE=1 python3 firmware/local-build/trackball-profile/test_profile.py
PYTHONDONTWRITEBYTECODE=1 python3 firmware/local-build/trackball-profile/test_capture.py
```

构建的原始 UF2 位于各自 build 目录的 `zephyr/zmk.uf2`。顶层发布别名与 JSON 在
本地核验后另行保存，构建不会自动覆盖已交付的顶层 UF2。

## 鼠标点击与滚动的现有键位

以下来自当前 `touch_modes.keymap`，需要 Dongle 使用本项目 MAC-DV / WIN-DV / GAME
版本；不是右侧诊断版新增的按键，也不证明用户当前 Dongle 的实机按键已全部验收。

| 功能 | MAC-DV / WIN-DV | GAME |
|---|---|---|
| 进入 FN | 按住左外拇指 | 按住右外拇指 |
| 左键/拖拽 | 左中拇指；按住可拖拽 | 右内拇指；按住可拖拽 |
| 右键 | FN + 右内拇指 | FN + 右内拇指 |
| 纵/横滚动 | FN + 左中拇指，同时转球 | 同左 |
| 慢速精确指针 | FN + 左内拇指，同时转球 | 同左 |
| 中键（按下滚轮） | 尚未绑定 MB3 | 尚未绑定 MB3 |

页面滚动与中键是不同事件：前者为 wheel/hwheel，后者为 MB3。
左键采用直接 mouse-button 行为，便于双击和保持拖拽，不再加一次长按判定。

## 社区参考与下一步交互建议

[ZMK mouse emulation](https://zmk.dev/docs/keymaps/behaviors/mouse-emulation) 提供 MB1/2/3
和滚动行为；[Charybdis 官方交互](https://docs.bastardkb.com/fw/charybdis-features.html)
包含精确模式、按住/切换 drag-scroll 和自动鼠标层。这些是可借鉴的交互，官方
Argos/QMK 的全部运行时设置不等于当前 ZMK 项目已支持。

建议先保留独立、直接的左键和显式按住滚动；稳定后补中键、可选滚动锁定。
自动鼠标层会影响移动后立即打字的行为，放在后续单独验收。以上新增绑定/切换
尚未实施，本轮不改动键盘字母、拇指键和输入模式。

用一体轨迹球替代日常办公鼠标是合理的使用目标；验收应覆盖文本精细选择、拖放、
长网页滚动、横向滚动及两台主机切换。FPS 等场景是否能完全替代需要实测，不由
具备鼠标按键或理论报告率直接保证。

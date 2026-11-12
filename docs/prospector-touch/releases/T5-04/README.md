# T5-04：输入链路定位候选（本地通过，实机待验收）

针对右侧连续运动卡顿、静止球快速输入也疑似缺字的问题。
修正 UI 线程访问，加入双端低频计数、USB/排队耗时，保留原 BLE 配对。
不宣称本次已解决实机卡顿。操作、MAC-DV 鼠标入口及电量新问题见
[诊断步骤](../../archive/history/docs/17-input-pipeline-debug.md)。

当前只有右侧组装。2026-11-01 用户希望暂缓鼠标按键/拖拽测试，
建议先使用 **原键位 Dongle q64**，收集集中接收与 USB 输出日志。
需要右侧鼠标入口时再使用 RIGHT TEST；它只在 NAV 增加右侧可用的左键、右键、
滚动与慢速入口。q5 保留用于严格对比，不要求一次刷完所有候选。

| UF2（`firmware/build/`） | 目标 | FLASH / 静态 RAM | SHA-256 |
|---|---|---|---|
| `prospector-dongle-pipeline-q5.uf2` | Dongle，原键位，5 项接收队列 | 541076 / 220762 B | `e5b6072444c9c3663699977ce1a4881102580defc0818f0703c67500dd7ebfae` |
| `prospector-dongle-pipeline-q64.uf2` | Dongle，原键位，64 项接收队列 | 541076 / 222178 B | `79e7c27cb6bee801e701183b5037884530cfa2a8a807e52d0bc4c5a691418f46` |
| `prospector-dongle-pipeline-q64-right-test.uf2` | Dongle，RIGHT TEST | 541076 / 222178 B | `a4843f3962c197774dcd90c8ececf47db5a2d22544d92fc0e530533cbe9ad3e9` |
| `prospector-right-pipeline-8ms-angle15.uf2` | 右侧 BLE 外设，保留 15° | 239792 / 52392 B | `64edfddb35b7aa0914ffce35588b33516270109021b6836cbcaa7f23f8a56ae4` |
| `prospector-right-pipeline-8ms-angle40.uf2` | 右侧 BLE 外设，总角度 40° | 239740 / 52392 B | `c59ed0e2e2d77f2b8d9048549bf85802b0f725f44b3a532a7ed53be1025633ff` |

所有 UF2 地址校验通过：Dongle `0x26000–0xAA200`，距旧 Bootloader 上限余 11776B；
右外设 `0x26000–0x60900`，余 313088B。不自动刷写、不更改 Bootloader、配对或充电设置。
静态 RAM 已包含 LVGL 池/静态线程栈，仍需实机观察运行时余量，不以链接成功代替运行验收。

设备页 SOURCE ID：q5 `97D454`、q64 `ADFC37`、RIGHT TEST `141ECF`。
设备页 KEYMAP：前两者 `TOUCH MODES`，右侧测试版 `RIGHT TEST`。
这是工作树内容标识，不是 Git SHA。

源码基准：firmware `87f6248`，module `6299108`，加本轮未提交改动；
ZMK `4dd95d7`、Zephyr `10ba6d0`、PMW driver `f6e2343`。
原 West ZMK/PMW checkout 保持干净；诊断插桩在受生成标记保护的隔离副本中进行。
JSON 逐份记录 UF2 校验、真实配置/DTS、私有 ZMK 补丁、模块工作树源文件摘要。
日志采集器后续单独改善了零输出提示，不影响已经生成的 UF2。

## 本地验证

- 五份 Docker/West 单目标编译、UF2 范围检查：PASS。
- 实际插桩函数的队列满、100ms 等待、GATT 失败、USB 信号量超时/端点错误注入：PASS。
- 隔离源码标识使用补丁清单，未记录的 core 改动会被拒绝：PASS。
- 实际 PMW 报告/定点旋转 C：15°/40° × 8ms/12ms，慢运动小数、反向、饱和、迟到采样：PASS。
- 真实 LVGL 三布局状态、WPM 定时器、120 次布局切换：PASS。
- RIGHT TEST 仅四个 NAV 绑定变化，实际编译 DTS 的 MB1/MB2/SCROLL/SLOW 目标：PASS。
- 真实串口采集器 PTY 数据、UTF-8 分片、已有文件保护、零输出 exit 3：PASS。
- q5/q64 有效 Kconfig 仅中央队列容量不同；右侧两版有效 Kconfig/DTS 一致、仅旋转系数不同：PASS。
- 两份新右侧版尚无刷写反馈；2026-11-01 用户已把运行 T5-03 8ms 的右侧接电脑，
  成功取得 PMW 日志。初始化/采样有正面证据，端到端可靠性仍待双端诊断。

## 复现

```bash
bash firmware/docs/prospector-touch/scripts/build-pipeline.sh
PROSPECTOR_PIPE_QUEUE=64 bash firmware/docs/prospector-touch/scripts/build-pipeline.sh
PROSPECTOR_PIPE_QUEUE=64 PROSPECTOR_RIGHT_ONLY_MOUSE=true bash firmware/docs/prospector-touch/scripts/build-pipeline.sh
PROSPECTOR_PIPE_TARGET=right PROSPECTOR_POINT_ANGLE_DEG=15 bash firmware/docs/prospector-touch/scripts/build-pipeline.sh
PROSPECTOR_PIPE_TARGET=right PROSPECTOR_POINT_ANGLE_DEG=40 bash firmware/docs/prospector-touch/scripts/build-pipeline.sh
```

脚本输出在每个同名 build 子目录 `zephyr/zmk.uf2`；顶层交付别名经单独校验复制。
回退 UF2 保留不覆盖。待用户确认输入、方向、触控和日志后，再决定正式默认参数/提交发布。

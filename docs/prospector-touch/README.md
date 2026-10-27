# Prospector Pro — Project Handoff / 本地开发交接包

**截至：2026-10-23 | Status: ZMK firmware compiled & display boots on actual device.**

**2026-10-24 更新：** 用户已确认三布局循环、下滑亮度、设备页及双重确认进入 NICENANO 正常。
T5-01 的 MAC-DV / WIN-DV / GAME 已实现并通过本地测试，尚待实机验收；真实键盘已到手，左右均为 nice!nano v2 兼容 nRF52840，
尚未刷入和配对。最新候选固件、本地验证与实机待测状态见 `docs/06-roadmap-and-acceptance.md`；
键位、模式切换及首次配对见 `docs/11-input-modes-guide.md`。下面的“已验证 CI”及早期缺口为交接时历史记录。

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
[候选版本记录](releases/T5-01/README.md)，候选状态与实机验收分别记录。

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

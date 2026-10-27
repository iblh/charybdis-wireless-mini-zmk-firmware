# 仓库整理与提交验证 — 2026-10-26

项目保持两个独立仓库，当前分支均为 `feat/touch-no-sensor`：

- firmware：硬件覆盖、键位、构建矩阵及 `docs/prospector-touch/` 中的交接文档、
  构建/校验脚本和原始 CI 历史证据。
- module：显示驱动、触控 UI、布局生命周期、亮度/设备/输入模式服务、字体处理及主机测试。

工作区原 `prospector-pro-handoff` 保留为指向正式文档目录的快捷路径；之前给出的
固件复制命令及读回命令仍适用。新 clone 直接使用正式的 `firmware/docs/prospector-touch/` 路径。
工作区根目录本身不作为第三个源码仓库提交，避免混入其他项目。

`config/west.yml` 固定测试依赖：

- ZMK：`4dd95d7840eb3d5a3f59bb29fbf1ab054715ef85`
- PMW3610：`f6e234367b22508b5c0a6bcc82437c64f320089b`
- Prospector module：`65b296d778c5b3261aa21927245cfd0fe922798e`
- Zephyr 由 ZMK manifest 导入，当前本地为 `10ba6d0cb38bc3d258775d27982f707599320085`。

完整 GitHub 构建矩阵新增一个 Touch modes central 目标；外设继续使用已有 QWERTY
目标传送位置事件。no_sensor Touch 和新 modes 的 central UF2 在上传前检查旧
Bootloader 的 `0xAD000` 写入上限。本次未触发完整 GitHub Actions 矩阵。

提交前本地验证：

- 真实设备服务 C（普通 QWERTY 和三输入模式配置）：PASS。
- 真实模式 worker、编辑行为，以及原生 ZMK mod-morph 的 36 位置 × 256 修饰键组合 ×
  两个系统模式 × 两种释放顺序：PASS（平台/HID 通过 host shim，不宣称真实键盘通过）。
- 788 个保留字形经真实 LVGL C 解码器与原像素一致：PASS。
- 实际 LVGL 页面事件/定时器回归，三个布局同时分配，模式选择与双重确认刷机：PASS。
- 正式脚本路径的 Docker/West 单目标构建 PASS：FLASH 500,880 B，静态 RAM 211,714 B；
  UF2 `0x26000–0xA0500`，距旧 Bootloader 上限余 51,968 B。
- GitHub 构建矩阵配置路径、工作流 YAML/内嵌脚本语法及依赖固定检查：PASS。
- 原路径与正式路径均可定位 workspace；本地文件模拟读回命令 PASS，未访问硬件。

`firmware/build/`、West 依赖、Git 元数据与渲染缓存不提交。
`releases/T5-01/` 只保存原候选的校验清单和 mock 预览；原始成功 CI 的小型 UF2/ZIP
作为历史证据保留。用户当前 UF2 文件没有被本次复现构建覆盖或自动刷写。

用户已确认 T4-01 设备页和双重确认进入 NICENANO。T5-01 的新映像启动、真实键盘
输入、左右 BLE 配对、快捷键、GAME 和轨迹球仍待实机验收。本次代码推送不是正式硬件验收。

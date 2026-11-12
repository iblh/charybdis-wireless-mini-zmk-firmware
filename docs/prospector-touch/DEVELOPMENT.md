# 开发指南

## 源码与边界

工作区为`firmware/`、`module/`两个Git仓库，均使用`feat/touch-no-sensor`。
firmware负责硬件overlay/conf、键位、依赖与构建；module负责UI、亮度、行为、扫描策略和测试。
`pcb/`是用户硬件资料。文档和`archive/reference/`不是可覆盖live源码的补丁；不要运行旧apply_patch.py。

改代码前先检查两个仓库status/branch，保留用户本地修改。固定运行时代码module提交：
`1345b3e91e23b8686f2b8b3e121515c6b3e52e84`；ZMK `4dd95d7840eb3d5a3f59bb29fbf1ab054715ef85`；
PMW模块 `f6e234367b22508b5c0a6bcc82437c64f320089b`。以`firmware/config/west.yml`为准，不更新浮动main。
后续文档提交不要求改动运行时依赖pin。

## 硬件与资源

Pro Micro nRF52840 / nice!nano-v2兼容板，Waveshare ST7789V2 240×280＋CST816T(I²C 0x15)。
无环境光传感器，已打印外壳不改。引脚以实际overlay为权威，不能替换成上游默认图。

| 信号 | GPIO |
|---|---|
| LCD DIN / CLK / CS | P0.22 / P0.17 / P0.24 |
| LCD DC / RST | P1.04 / P1.06 |
| Touch SDA / SCL | P1.00 / P0.11 |
| Touch RST / IRQ | P1.13 / P1.15 |
| LCD BL | P0.29 PWM，已实测真实调光 |

LCD_BL不能同时接3.3V和PWM。触屏映射已按270°显示方向修正双轴镜像。

nRF52840为256KiB RAM；目标LVGL堆固定64KiB，partial buffer，亮度三布局共享一个顶层面板。
32位真实LVGL测试报告峰值36448B，120次开关无保留增长、120次切屏通过；64位64KB失败不能算通过。
目标Bootloader0.6.0应用范围`0x26000..<0xAD000`，共552960B，必须核验UF2，不能只看链接器FLASH容量。
T5-12静态RAM225320B、链接FLASH523564B，UF2末端0xA5E00、可写余29184B。

## 本地构建

需要Docker Desktop和已固定West依赖。从两个仓库的共同父目录执行：

```bash
bash firmware/docs/prospector-touch/scripts/verify-workspace.sh
PROSPECTOR_STUDIO_USB=true PROSPECTOR_KEYMAP=touch_modes SKIP_WEST_UPDATE=true \
  bash firmware/docs/prospector-touch/scripts/build-touch-only.sh
```

首次获取依赖时省略`SKIP_WEST_UPDATE=true`。这是单目标Dongle构建，不运行39项矩阵。
输出`firmware/build/prospector-touch/zephyr/zmk.uf2`；清理前将确需交付的文件复制到明确角色文件名，保留SHA清单。
左右外设可分别构建：

```bash
PROSPECTOR_PERIPHERAL_SIDE=left bash firmware/docs/prospector-touch/scripts/build-touch-peripherals.sh
```

不要把普通右侧构建误当800CPI诊断版：右侧当前还使用历史诊断/校正pipeline，正式无诊断版尚待开发。
该pipeline和历史命令保存在`local-build/trackball-profile/`以及[历史分析](archive/history/docs/27-current-baseline-and-next-steps.md)。

任何交付UF2都必须运行：

```bash
python3 firmware/docs/prospector-touch/scripts/verify-dongle-uf2.py /absolute/path/to/target.uf2
```

构建脚本也会核查实际ELF的BLE/settings→central→observer顺序。没有明确授权不运行west flash、Bootloader写入或全局settings_reset。

## 本地测试与发布

针对相应改动运行已有native：`module/tools/test_device_service.py`、`test_input_modes.py`、
`test_scan_policy.py`、`test_scan_startup.py`、`test_left_slot_recovery.py`、`test_peripheral_state.py`。
这些C测试需要可用的C编译器。真实LVGL堆测试入口是`module/tools/test_controls_heap_container.sh`，
Linux builder内需gcc/g++-multilib及qemu-user；32位、64KB池验证UI，不用截图占用代替目标运行时占用。

```bash
python3 firmware/docs/prospector-touch/scripts/package-release.py firmware/docs/prospector-touch/releases/v0.1.0-rc1/manifest.json
```

打包只接受清单中原UF2的精确SHA，校验UF2并回读ZIP。现有RC包保持原SHA，整理文档不重打或替换远端已上传文件。
正式stable前需移除右侧诊断并回归；Build PASS、UI启动、触摸、BLE连接、HID、长期验收分别记录。

## 文件保留与清理

- `build/`现在只保留四个UF2、README和`releases/`。以后构建仍会生成缓存，可以在交付文件/证据保存后删除。
- `.local-artifacts/reports/`保存原始log/ZIP；`.local-artifacts/history/`保存先前归档与历史UF2；
  `build-evidence-2026-11-12.tar.gz`保存本轮ELF/map/配置/DTS/生成源。Git忽略这整个本地目录。
- CMake对象、静态库、host renderer缓存及已生成暂存app已删除，下次构建会重新生成，耗时相应增加。
- West依赖`zmk/zephyr/modules/optional/`仍保留，避免重新下载；不要因体积大就当作无用内容删除。
- 历史文档在`archive/history/`，原CI在`artifacts/`；版本清单在`releases/`。

[当前状态](STATUS.md) · [使用指南](USER-GUIDE.md)。

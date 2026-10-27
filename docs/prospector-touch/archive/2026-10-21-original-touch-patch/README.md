# Prospector Touch Edition — 无环境光传感器的实施包

**定位：** 对已成功在 Arduino 测试 SPI LCD + I²C Touch 的 Pro Micro nRF52840（nice!nano v2 兼容板），基于 280Zo 的无线 Charybdis Mini 3×6 / Prospector 固件，提供硬件引脚重映射与 LVGL 触屏亮度设置的**源码补丁**。外壳已打印，不包含 3D 打印与机械装配说明。

> **诚实的完成度声明：** 此包已经核对上游源码 API、引脚和 Zephyr 4.1 DTS 名称，并使用 Python 检查补丁脚本语法，但尚未运行 Zephyr CI 编译、实机验证 LVGL 触控/UI 或 BLE 配对。不能声称这是已经过验证的一键烧录成品。正式固件需要在你的 GitHub forks 中构建并检查编译日志。四种布局仍是 **编译时** 选择，真正的运行时四布局无缝切换需要进一步重构原模块的 widget 生命周期，不能靠添加一个触控下拉框实现。

## 目标与已知硬件

- 主控：Pro Micro nRF52840, pinout compatible with nice!nano v2, 2021 bootloader 0.6.0 with `NICENANO` UF2 volume, S140 6.1.1.
- 屏幕：Waveshare 1.69in Touch LCD SKU 27057，ST7789V2 240×280，CST816T `0x15`。
- LCD SPI / I²C 已在 Arduino IDE 成功验证（实际坐标/IRQ 尚未验证）。
- 不接环境光传感器；所有背光调节为手动；外壳已打印。
- 适配候选键盘：Wireless Charybdis Mini 3×6；若你的最终键盘不同，固件 shield / peripherals 必须调整。

## A. 与你原来接线完全一致的信号

| LCD/Touch | nRF GPIO | 备注 |
|---|---|---|
| LCD_DIN | P0.22 | SPI MOSI |
| LCD_CLK | P0.17 | SPI SCK |
| LCD_CS | P0.24 | active-low |
| LCD_DC | P1.04 | |
| LCD_RST | P1.06 | |
| TP_SDA | P1.00 | Zephyr I²C1 重新映射 |
| TP_SCL | P0.11 | |
| TP_RST | P1.13 | |
| TP_IRQ | P1.15 | **必须新增这一根线才能用 IRQ 驱动** |
| LCD_BL | 3.3V 当前接法 | **手动亮度功能需要改线**，目标 P0.29 PWM（可能需要驱动晶体管）；严禁同时接 GPIO 与 3.3V。 |

电气提醒：LCD_BL 是背光控制输入，必须核对 SKU 27057 的原理图/实测控制电流，再决定由 P0.29 直连还是使用 MOSFET/电平缓冲。任何时候不要把 3.3V 电源脚当 GPIO；拔电源再改线。

## B. 源码分层与已覆盖的功能

- 上游 `280Zo/charybdis-wireless-mini-zmk-firmware`：Charybdis 左右 Peripheral + Central shield、PMW3610 trackball、Keymap、CI、Zephyr/ZMK 构建。
- 上游 `280Zo/prospector-zmk-module`：4 个静态布局、状态 widget、ZMK/USB HID、`&pbl` 手动亮度 API、自动 backlight blanking。
- **本补丁新增：** 重映射 GPIO、Zephyr CST816S 输入设备 + LVGL pointer、显示上的 `SET` 按钮、触控亮度 slider、滑动打开关闭设置、Settings 命名空间中持久化亮度。
- **未实现/需要进一步工程化：** 触摸唤醒 ZMK Idle 后屏幕、LVGL 非阻塞亮度处理、运行时四布局切换、动态修改 sleep time / rotation、触控校准、BLE 配对菜单、压力/长时间测试和真实硬件构建。不要以为这些已写进源码。
- Ambient light **不包含**，原模块传感器配置仍设为 `n`。

## C. 从零建立 GitHub Fork + 补丁工作区

先在 GitHub 网页上分别 Fork 两个上游仓库到自己账号：

1. https://github.com/280Zo/charybdis-wireless-mini-zmk-firmware
2. https://github.com/280Zo/prospector-zmk-module

```bash
mkdir -p ~/Workspace/Lab/prospector-pro
cd ~/Workspace/Lab/prospector-pro
# USER 是你的 GitHub 用户名
USER="YOUR_GITHUB_USERNAME"
git clone "https://github.com/$USER/charybdis-wireless-mini-zmk-firmware.git" firmware
git clone "https://github.com/$USER/prospector-zmk-module.git" module
cd firmware && git checkout -b feat/touch-no-sensor && cd ..
cd module && git checkout -b feat/touch-no-sensor && cd ..

# 另在 ~/Downloads 解压本实施包（或修改此路径）：
PATCH_DIR="$HOME/Downloads/prospector_touch_package"
python3 "$PATCH_DIR/scripts/apply_patch.py" \
  ~/Workspace/Lab/prospector-pro/firmware \
  ~/Workspace/Lab/prospector-pro/module
```

脚本会在 `firmware` 中加入两个配置文件、只给 `dongle_prospector_nano_no_sensor` 这个 build 添加 conf/overlay；在 `module` 中添加触控 UI 源码/Kconfig/CMake 并对四个 `status_screen.c` 插入条件性 UI hook。脚本只处理上游对应的已知结构，遇到未知结构会停止，不会盲目替换其他版本。

## D. 关键修改：让 firmware 使用你 Fork 的模块

在 `firmware/config/west.yml`，保留 ZMK、PMW3610 配置不变，修改 `prospector-zmk-module` 的 remote，例如：

```yaml
manifest:
  remotes:
    - name: zmkfirmware
      url-base: https://github.com/zmkfirmware
    - name: 280Zo
      url-base: https://github.com/280Zo
    - name: yourname
      url-base: https://github.com/YOUR_GITHUB_USERNAME
  projects:
    - name: zmk
      remote: zmkfirmware
      revision: main
      import: app/west.yml
    - name: zmk-pmw3610-driver
      remote: 280Zo
      revision: main
    - name: prospector-zmk-module
      remote: yourname
      revision: feat/touch-no-sensor
  self:
    path: config
```

上述 `revision` 是初次开发分支名。构建成功后，请固定到经过测试的 Git SHA，避免上游变化使构建不稳定。尽量将 ZMK 固定到上游 firmware 仓库已确认兼容的版本/commit。

## E. 配置代码说明

- `firmware/config/dongle_prospector/dongle_prospector_touch.overlay`: GPIO 重映射、I2C1、CST816T、Zephyr LVGL pointer、PWM。
- `firmware/config/dongle_prospector/dongle_prospector_touch.conf`: 启用输入、Zephyr 触控驱动、手动亮度、闲置 300 秒、保存设置所需支持。上游 `common.conf` 设了 30 秒 idle，我们配置放在最后覆盖为 300 秒。
- `module_fork/.../touch_settings.c`: 增加 `SET` 入口和亮度滑块，松开滑块后写设置，避免每个像素移动都写闪存。
- 正在使用的 ZMK 键盘是 Peripheral，Prospector Dongle 是 Central，因此你的键盘两侧也必须烧录对应的 dongle 版本，不能只刷 Dongle。

## F. 构建、UF2 烧录

```bash
cd ~/Workspace/Lab/prospector-pro/module
git add .
git commit -m 'Add touch settings UI for no-sensor Prospector'
git push -u origin feat/touch-no-sensor

cd ../firmware
git add .
git commit -m 'Configure touch Prospector for proven Pro Micro pinout'
git push -u origin feat/touch-no-sensor
```

注意 GitHub Actions 通常在 Fork 的默认分支/main 的工作流中有对 PR 分支的触发约束；如果没有自动运行，打开 Fork 仓库 Actions 栏，按仓库 `build.yml` 的 `workflow_dispatch`/分支配置触发构建，必要时把 PR 合并到 main 后再运行。首轮构建失败需要依据具体日志调整 DTS Kconfig，不能机械地删除错误选项。

查找 `dongle_prospector_nano_no_sensor` 对应 artifacts，根据 build.yaml 中的 QWERTY/Colemak 选择；最终正常的 ZMK nice!nano 构建一般会输出 UF2 供 `NICENANO` 盘拖放使用。构建产物并不是这里提供的 ZIP。

在你已证实能挂载 `NICENANO` 的开发板上：

```bash
ls /Volumes/NICENANO/INFO_UF2.TXT
cp -X path/to/BUILT_DONGLE.uf2 /Volumes/NICENANO/
```

不要执行 `Burn Bootloader`。复制后磁盘可能因开发板重启消失；使用屏幕、键盘 HID 等真实行为验证启动结果。若无法启动，双击 Reset 恢复到 UF2 模式并刷入上一次能够工作的固件。

## G. 键盘与 Central 配对（Charybdis Mini 3×6 情况）

1. **备份**你键盘当前仓库、keymap，以及仍然可用的 BT 固件。完成新的 Dongle 构建并确认能启动之前，勿更改键盘两侧固件。
2. 先准备齐全的 `charybdis_left_dongle`、`charybdis_right_dongle`、`charybdis_dongle prospector_adapter` 三个 UF2，确保与同一个 Keymap 和相同 ZMK 基线对应。
3. ZMK 官方要求转换为新的 dongle 架构之前，给 Dongle 和两侧键盘各运行一次相应的 `settings_reset` 固件，以清理旧 BLE Bond；会删除相关配对数据。
4. 恢复烧录目标 Dongle UF2，随后依次烧入左右 Peripheral UF2。
5. 先上电 Dongle，再上电左侧，确认连接，再上电右侧；原电量 widget 按配对顺序显示两侧电量。
6. 使用电脑测试 USB HID、全部按键、Layer、电量、PMW3610 trackball（如适用）、断开和重新连接。

参考 ZMK 文档：https://zmk.dev/docs/hardware-integration/dongle

## H. 真正的“正式版”还需完成的工程设计

1. **设置 UI**：定义可复用的设置状态机：HOME, SETTINGS, DIAGNOSTICS, CONNECTION；所有 UI 动作通过 ZMK/Zephyr 工作队列异步执行，触控驱动不可阻塞 BLE/HID。
2. **休眠唤醒**：设计 Touch IRQ 唤醒时先点亮背光、只消费唤醒触摸不触发设置按钮；应符合 ZMK `ACTIVE`/`IDLE` 状态，不要直接绕过原有 ZMK Display blanking。
3. **全布局动态切换**：原模块四布局为互斥 Kconfig choice，当前不能实时切换。需要拆出 `layout_create()/destroy()` 接口，为不同布局重命名同名 widget 或做一层布局注册表，订阅相同 ZMK 状态事件；切换时完整销毁旧 LVGL screen/widget、解除回调和清理定时器；先评估 256KB RAM 的峰值占用。
4. **Brightness 持久化与平滑**：当前触控源码直接调用亮度渐变，可能导致短暂 UI 延迟；生产版应在独立 k_work 上进行 PWM ramp，并只在 slider release 保存到 Zephyr Settings。
5. **可变休眠时间**：现在 `CONFIG_ZMK_IDLE_TIMEOUT` 是编译时值。触控动态设定休眠时间需要改造独立屏幕 Idle 计时器，不应向用户显示虚假的可运行时调整选项。
6. **触控验证**：Zephyr 4.1 驱动只接受部分 CST816 chip ID。当前 Arduino 能 I²C ACK，不等于 Zephyr 驱动必定 probe 成功；必要时验证寄存器 `0xA7`，决定是否扩展 ID 或 reset/IRQ 策略。
7. **诊断与压力测试**：各场景下测量 zmk busy rate、堆栈峰值、USB / BLE 丢键、跨 100 次重连、长时运行及设置持久化；失败时屏幕可降级但 HID 应继续可用。

## I. 测试矩阵

- UF2 能启动，不改 MCU Bootloader；UI 无黑屏/色彩异常。
- 显示能实时跟随键盘 Layer、Modifier、电量、WPM；PMW3610/鼠标操作正常。
- 触控设置按钮可打开；Slider 能改变真实背光（而不是只改变像素亮度），重新上电后值保留。
- 手动模式 1–100% 可控，空闲 5 分钟熄屏，输入活动恢复背光；触摸唤醒作为正式版验收项。
- 触控 IRQ 和渲染不造成 BLE 丢键；断线能重连。
- 若要支持四布局实时切换，必须在同一刷入固件中实现，而不是通过四个 UF2 重刷来伪称完成。

## J. 上游参考

- https://github.com/carrefinho/prospector
- https://github.com/carrefinho/prospector-zmk-module/tree/feat/new-status-screens
- https://github.com/280Zo/charybdis-wireless-mini-zmk-firmware
- https://github.com/280Zo/prospector-zmk-module
- https://zmk.dev/docs/hardware-integration/dongle
- https://www.waveshare.com/wiki/1.69inch_Touch_LCD_Module

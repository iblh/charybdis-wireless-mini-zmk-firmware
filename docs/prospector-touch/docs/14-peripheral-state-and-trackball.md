# T5-02：布局状态、左右显示与轨迹球诊断（2026-10-27）

## 用户实机反馈

- 左右外设已经刷入并通过 Dongle 正常打字，键位初步看起来正确；完整快捷键与 GAME 验收尚未完成。
- 从连接时的 Operator 切换外观后，新页面的连接/电量状态有时不更新；电脑仍能打字。
- 右键盘显示在左指示器，左键盘显示在右指示器。
- 右侧为 PMW3610，电池供电完全不移动鼠标；USB 供电、单按 Reset 重启后也完全不动。

## 显示端根因与改动

原控件缓存的是最后一次单槽事件。其他布局首次创建时，用 NULL event 初始化为
slot 0 / disconnected / battery 0，未重建已经连接的两个槽；连续事件合并到一个
显示 work 时，也可能仅留下最后一个槽位。Operator 的初次更新还发生在控件加入
更新列表之前。因此切换外观不能可靠继承已经存在的外设状态。

T5-02 从共享连接观察器和 ZMK 电量缓存读取两个槽的完整快照；创建布局和更新
布局走同一路径，刷新覆盖全部槽位。连接状态在发布事件前原子更新，忽略未跟踪
连接的断开事件。Operator 先注册控件再做初次刷新。

物理左右不由蓝牙槽号自动定义。本次按用户报告的当前绑定顺序，设置
`CONFIG_PROSPECTOR_LEFT_PERIPHERAL_SLOT=1`：左图示用 slot 1，右图示用 slot 0。
这只改变 UI 顺序；设备页 K1/K2 仍为原始槽号。正常重启不改变此配置；若以后重新
配对导致槽号顺序变化，需要重新核对这个设置，不应通过清除配对来纠正 UI。

键位和轨迹球处理链路未因本次显示修复改变，左外设继续使用当前正常固件。

## 本地验证与新 Dongle 文件

- 真实连接观察器 + 快照查询 C 的 host 测试：两种左右映射、初次读取、双槽合并更新、
  状态先提交再通知、断开/重连、忽略无关连接，PASS。
- 实际 LVGL：先连接两侧，再首次创建 Classic/Field；验证两个电量及真实左右坐标；
  合并刷新、断开/重连以及不重连 BLE 的 120 次切屏，PASS。
- 既有模式选择、双重确认刷机、模式 worker 和设备服务回归，PASS。
- 本地 Docker/West Dongle PASS：FLASH 500,488 B，静态 RAM 211,602 B（80.72%）。
- UF2 范围 `0x26000–0xA0400`，距旧 Bootloader `0xAD000` 余 52,224 B，PASS。

候选：`firmware/build/prospector-touch-peripheral-sync.uf2`，T5-02，SRC **93CC06**。
SHA-256：`43ce36cfb6475af1d94b85758471771ceb9f2135bce9beaabea83f426bbe0be1`。
同名 `.json` 和 [版本记录](../releases/T5-02/README.md) 含完整清单。
**这些是本地检查，新固件的实机验收仍待用户确认。**

通过 Dongle 设备页进入 NICENANO 后：

```bash
cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-touch-peripheral-sync.uf2' /Volumes/NICENANO/
```

回到应用后，让两侧保持连接，在三个外观间切换，确认连接/电量立即一致；分别关掉
一侧观察物理左右指示器，再恢复供电。切屏期间也确认打字继续正常。

## 轨迹球：当前结论与诊断版

正常右侧固件已启用 PMW3610 驱动、SPI/IRQ 和 input-split，Dongle 已启用对应
输入代理和 input-listener。仅凭按键能打字，无法证明传感器初始化或运动数据正常。
USB 与电池均完全不动，仍须读取传感器日志区分初始化、运动 IRQ/光学和 BLE 转发。

驱动自身的 README 记载了 nice!nano 上可能出现电源稳定时序导致产品 ID 错误的情况，
但本机尚无该错误证据；本轮没有改传感器引脚或启动延时，不能宣布轨迹球已修复。

临时右侧诊断版：`firmware/build/prospector-right-trackball-diagnostic.uf2`。
它保持 BLE 外设角色和原 PMW3610 配置，增加 USB CDC 串口及传感器 DEBUG 日志；
日志输出延迟 10 秒，CDC 缓冲 8192 B，LOG 缓冲 16384 B，便于看到上电记录。
它不会作为 USB 键盘直接向电脑发送按键。日志增加额外开销，诊断结束可刷回正常右侧版。

本地构建 PASS：FLASH 236,712 B，RAM 74,392 B；UF2 `0x26000–0x5FD00`，
距 Bootloader 上限余 316,160 B。已核对 peripheral role、USB 日志、PMW DEBUG、
原额外上电延时 0ms；**物理诊断结果待采集**。
SHA-256：`64644f7d415a34508138686558f8946e8166b79d710686d2f3f133c940307f7f`。

### 在 macOS 采集右侧日志

1. 暂时拔下 Dongle，只接右侧主控 USB；双按右侧 Reset，确认 NICENANO 是右侧主控。
2. 复制日志版（这条命令只用于右键盘）：

   ```bash
   cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-right-trackball-diagnostic.uf2' /Volumes/NICENANO/
   ```

3. 自动重启后，在终端列出串口：

   ```bash
   ls /dev/cu.usbmodem*
   ```

4. 将下面的占位路径替换成刚出现的右侧串口完整名称：

   ```bash
   screen /dev/cu.usbmodemXXXX 115200
   ```

   如果有多个不确定的端口，先确认哪一个随右侧 USB 插拔出现/消失。
   保持右侧 USB 供电，等待约 10 秒，然后滚动轨迹球。
5. 保存/贴回 PMW3610 初始化及运动相关日志，尤其是：
   `PMW3610 initialized`、`initialization failed`、`Failed self-test`、
   `Incorrect product id`、`SPI burst read failed` 或 `x/y:`。
   为测试转发，可在串口已识别后把 Dongle 插回电脑，继续滚动。
6. 退出 screen：Ctrl+A，然后 K，再按 Y。

日志决定下一步：

- 自检/ID/SPI 读取失败：检查上电稳定、引脚/连线和供电，不直接归因于硬件损坏。
- 初始化成功、没有运动日志：继续检查 motion IRQ、光学/安装或驱动触发路径。
- 出现非零 X/Y、电脑仍不移动：检查 input-split 订阅、中央处理器和 USB 鼠标报告。

正常右侧回退文件仍为 `firmware/build/prospector-touch-right-peripheral.uf2`；
Dongle 上一版本仍为 `firmware/build/prospector-touch-input-modes.uf2`。
本轮没有清除配对、没有更新 Bootloader，也没有实际向任何设备刷写。

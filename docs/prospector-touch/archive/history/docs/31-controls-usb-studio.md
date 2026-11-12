# T5-12：控制页改版、第二次更换左主控和 USB Studio

2026-11-10 本地候选；2026-11-12用户确认已自行刷入、没有问题、左右均能连接。没有自动刷写硬件。用户确认这次是在 v1 维护成功后又换了另一块左主控，右侧未变。

## 本次变化与边界

- DEVICE、模式选择、UF2确认页统一深色面板、细线边框、青色重点、分级字体。
  保留版本/SOURCE/构建时间、当前模式、USB/K1/K2状态以及原双重确认。
- BRIGHTNESS 使用大百分比和方形滑块，明确10%/100%边界；三个状态布局共用一个顶层面板。
  下滑打开、CLOSE关闭、左右切布局、上滑系统页的含义不变。
- 正常版增加 `USB EDITOR / UNLOCK`，接入标准 ZMK Studio USB RPC；默认锁定，断开连接后重新锁定。
  未启用 Studio BLE transport；保留r2的0/1/2连接扫描策略、ATT3和中央q64。
- 给自定义 Dvorak/QWERTY mod-morph 添加可读名称与模式/快捷键参数元数据，没有修改九层×41键的绑定。
- 右侧保持800 CPI/ATT3/8ms，不要求重刷。新左侧使用原正常左侧固件，不需要传感器或屏幕。

## 64KB测试如何解决

此前64位主机在64KB池内的测试失败，不能当作通过，也不直接等同于32位nRF52840耗尽堆。
本次将三个亮度面板合并为一份，并单独构建32位LVGL对象，在固定65536字节池内运行实际UI代码。
截图另用较大的主机池，因为一张ARGB截图本身约270KB，不属于目标固件运行时。

最终测试覆盖全部三个状态布局、九层配置、与目标一致的默认Montserrat12字体、设备/模式页、
USB锁操作、真实指针拖动、10–100%边界、双重确认与故障路径、120次页面开关、120次切屏及外设状态刷新。
断言只存在一个亮度滑块、重复开关没有保留堆增长，32位下最大连续空闲块至少8KB。
最终报告峰值36448B，测试末最大连续空闲块24788B；64位大池对照报告峰值57264B，
加上更大的池控制/分配块元数据后不适合拿同样64KB限额直接等同32位目标。
原64位64KB失败保留；目标配置仍是64KB，没有上调目标内存池。

复现（工作区根目录，Docker Desktop已启动）：

```bash
docker compose -f firmware/local-build/docker-compose.yml run --rm \
  -v "$PWD/module:/workspaces/prospector-local-module:ro" --entrypoint bash builder -lc \
  'apt-get update -qq && apt-get install -y -qq gcc-multilib g++-multilib qemu-user && bash /workspaces/prospector-local-module/tools/test_controls_heap_container.sh'
```

这是UI对象/绘制回归与堆预算验证，不等于实机无线并发、USB RPC栈峰值或长期稳定性测试。
ARM ELF仍单独核查静态RAM和FLASH；交付清单记录最终数值及所有UF2校验。

## 刷写顺序：新左侧 → 维护Dongle → 正常Dongle

右侧保持当前固件与配对，不重刷、不清全部绑定。左右两半分别与Dongle配对，左右之间不直接配对；
也不在macOS的蓝牙设置中操作。旧左侧主控必须断电并保持关闭。

1. 先拔掉Dongle的USB，避免把文件复制到错误的NICENANO盘。新左侧主控用数据线接电脑，快速双击Reset。
   确认只有这块板子的NICENANO挂载，运行：

   ```bash
   cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-left-link-test.uf2' /Volumes/NICENANO/
   ```

   这是正常左侧外设固件，裸板或已接左侧矩阵均使用它。刷完先断开新左侧电源。
2. 右侧保持供电；Dongle重新接电脑，从设备页FLASH双重确认进入NICENANO，复制**第二次替换专用**维护版：

   ```bash
   cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-dongle-left-slot-recovery-v2.uf2' /Volumes/NICENANO/
   ```

   设备版本应为 **T5-12-LEFT2 / SOURCE 26C690**。它使用 `prospector_left_repair/v2`，保留v1记录；
   仅删除存储的旧K2身份及其对应密钥，前后核对K1地址和密钥未变。
   首次成功后会自动重启一次，等待约10秒，再上滑查看 **LEFT CLEARED**。
3. 给新左侧供电，等待最多约60秒。预期 **K1 ON（右）/K2 ON（左）**。
   若有错误标签、K1不能重连或K2一直离线，记录完整设备页，先停止后续操作；不要反复清绑定。
4. 看到双侧ON后，再从Dongle设备页进入NICENANO，复制正常新版：

   ```bash
   cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-dongle-controls-usb.uf2' /Volumes/NICENANO/
   ```

   版本 **T5-12-USB / SOURCE A9EA70**。此正常版不编译左侧清理逻辑，配对结果会保留。
   v2维护文件只用于这次换板，日后再换主控不能靠重复刷它清槽。

如果复制末尾因板子立即重启出现 `Device not configured`，不要只看cp退出状态判定失败；
先看版本/启动。确有疑问才进入NICENANO只读核对：

```bash
python3 '/Users/paul/Workspace/Lab/prospector-pro/firmware/docs/prospector-touch/scripts/check-flashed-dongle.py'
```

不需要刷settings_reset，也不需要重新给右侧配对。原r2回退文件与旧维护文件保持原SHA。

## 用 ZMK Studio／KeyPeek 查看键位

旧版有USB CDC端口，但关闭 `CONFIG_ZMK_STUDIO`，所以能选端口却没有Studio服务响应。
[ZMK官方要求](https://zmk.dev/docs/features/studio#building)同时启用snippet和Studio配置，本版两者均已启用。

1. Dongle正常运行T5-12-USB，用**数据USB线接电脑**；键盘两半可电池或充电器供电。
   USB数据线连接哪块板，浏览器就访问哪块板；不要选择左/右外设端口。
2. 关闭 `screen`、日志采集脚本，以及其他正在连接此设备的网页。
3. 用Chrome或Edge打开 [ZMK Studio](https://zmk.studio/)，选择USB，再选 **Prospector Touch** 对应端口。
4. 网页提示Device Locked / Unlock To Continue时保持连接；Dongle主页上滑，在DEVICE页点 `USB EDITOR / UNLOCK`，随后显示 `USB EDITOR / LOCK`。
   先连接再解锁，避免连接过程重新上锁。连接后选择MAC-DV、WIN-DV、GAME及NUM/NAV/SYM/FN/SLOW/SCROLL层查看。
5. 查看完先断开Studio，再打开 [KeyPeek网页](https://srwi.github.io/keypeek/)，重复USB连接与解锁。
   同一串口同时只让一个网页/程序访问。

标准Studio解锁同时允许编辑；这不是固件强制只读模式。本次目的是熟悉布局，**不要改键、保存、重排/删除层或执行Restore Stock Settings**。
九层索引关联模式及轨迹球处理；本版没有验证用户任意编辑/重排后的兼容性。

`QUOTE / Q`、`P / R`等名称前项是Dvorak字符，后项是对应QWERTY快捷键；MAC-DV的Command/Control，
WIN-DV的Control/Alt会触发对应mod-morph。页面可能将自定义行为显示为名称而非单一字母。
[KeyPeek说明](https://github.com/srwi/keypeek#setup)区分网页键位查看/编辑与桌面实时层跟随；
本版不增加Raw HID notifier，不能保证桌面浮窗随物理按键自动切层。

连接失败时请记录：浏览器名称、所选USB设备名、网页完整错误、设备页版本和UNLOCK后的文字。
无需先重采无线日志或重置任何配对。

## 最简实机验收

- 配对与供电重连：K1/K2均ON；右侧先确认打字/滚球正常。左侧若已焊接矩阵，再逐键检查；裸板ON只算连接验证。
- 新页：三个布局左右循环；下滑打开亮度，10–100%真实调光/CLOSE；上滑DEVICE、模式切换、FLASH双重确认。
- USB：先Studio再KeyPeek读取键位；断开网页后继续打字和滚球，确认没有明显回退。
- 休眠：五分钟后黑屏、触摸唤醒。新Studio变体引入电源管理依赖，须重新做这一项实机回归。

本地Build/测试PASS和硬件PASS分别记录；用户已确认刷写后双侧连接；浏览器RPC、完整UI/休眠回归和长期稳定性单独验收。

构建命令：

```bash
PROSPECTOR_LEFT_RECOVERY=v2 PROSPECTOR_BUILD_NAME=prospector-dongle-left-recovery-v2 PROSPECTOR_KEYMAP=touch_modes SKIP_WEST_UPDATE=true bash firmware/docs/prospector-touch/scripts/build-touch-only.sh
PROSPECTOR_STUDIO_USB=true PROSPECTOR_BUILD_NAME=prospector-dongle-controls-usb PROSPECTOR_KEYMAP=touch_modes SKIP_WEST_UPDATE=true bash firmware/docs/prospector-touch/scripts/build-touch-only.sh
```

日志及校验清单：`firmware/build/reports/t5-12-*`、`releases/T5-12/`。未触发远程CI。

[资源、SHA及真实LVGL模拟预览](../../../releases/T5-12/README.md)。

2026-11-12补充：用户确认USB连接后收到标准锁提示，服务响应通过；解锁后完整读取待确认。
历史维护/旧回退UF2现已归档至`firmware/build/archive/2026-11-12-release-prep/uf2/`，不再混放build顶层。
已完成换板的用户不需要重复维护，当前包见 [RC1](../../../releases/v0.1.0-rc1/README.md)。

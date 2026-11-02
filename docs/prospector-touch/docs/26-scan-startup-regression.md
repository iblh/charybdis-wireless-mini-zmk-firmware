# T5-09B：修复扫描策略版的启动顺序回归

## 实机报告与根因

用户确认 T5-09 (`T5-09-SCAN / SOURCE 20BD12`) 屏幕正常，但右侧无法连接；
只回退 Dongle 到 T5-08 后即可恢复。旧文件已标记为有回归，保留作负向测试样本。
无需清除绑定，也不需要重新刷右侧。

T5-09 的模块 CMake 提前加入生成的 central.c 编译单元，改变了 app 链接顺序。
ZMK BLE 和 split central 原本都使用 APPLICATION / priority 50；相同优先级没有表达它们的依赖。
实际旧 ELF 中 central 的启动项在 `0x852dc`，BLE 在 `0x852e4`，因此 central 先执行。

执行链条：

1. central 初始化注册动态 Settings handler `ble_central`，其 commit 回调为 `finish_init`。
2. 随后 BLE 初始化调用 `bt_enable → bt_settings_init → settings_subsys_init → settings_init`。
   Settings 首次初始化会清空动态 handler 列表，之前注册的 `ble_central` 因此丢失。
3. main 中 `settings_load` 不会调用该 handler 的 commit，`settings_loaded` 一直为 false，
   split transport 不可用，不能启用扫描。显示和触控仍能正常启动。

这是动态回调注册的生命周期错误，并未擦除持久化的 BLE 配对记录。
源端 GPIO、CPI、ATT 缓冲和新的低占空比参数均不能解释或修复此启动问题。

## 修复边界

- 生成器显式将 central 设为 APPLICATION / 51，并断言固定 ZMK 版本的 BLE 优先级为50。
- Prospector 的连接状态观察模块随后在52初始化；未启用扫描策略的历史诊断构建保持原优先级。
- 最终 ELF 必须满足 BLE/settings → central → observer；普通本地构建加入强制检查。
  校验器读取真实 init entry 中的函数指针，不只检查源代码写了哪个优先级。
- 模块源码和生成后的 central 的扫描状态机不变。仍为0侧快速扫描、一侧5ms/200ms后台扫描、
  双侧停扫描，连接中暂停，保留自动发现和重连。
- 右侧保持800 CPI / ATT3 / 8ms / 顺时针15°；q64、双槽、连接参数、键位和接线保持原值。

## 本地证据与未验证项

- `test_scan_startup.py` 编译实际 central init / finish_init 函数，以 Settings 生命周期模型复现
  旧顺序的回调丢失和无扫描，验证 BLE 先初始化时能保留回调并启用 transport。
- 原扫描策略 native 测试通过，覆盖0/1/2侧、连接失败、停止失败清理、重试、竞争和状态变化。
- 旧 T5-09 ELF 被启动校验器拒绝；新版实际 ELF 为 BLE `0x852dc` → central `0x852ec` → observer `0x852f4`。
- 本地普通 Docker/west 单目标构建通过。FLASH 501672B、静态RAM 213442B。
- UF2 验证通过：`0x26000–0xA0800`，距离旧Bootloader限制余51200B。
- 实际 `.config` 对比旧 T5-09 仅版本标签变化；去掉构建目录路径差异后，DTS相同。
  生成central只改变初始化优先级并添加固定优先级断言。
- 旧问题文件、T5-08回退和右侧UF2的SHA-256保持原值，未自动刷写任何硬件。

**实机更新：** 用户已确认r2右侧自动连接和断电重连通过，轨迹球控制明显改善。
双侧发现/重连、长时间稳定性以及修复后定量帧间隔仍待验证。
本地通过不等于卡顿已消除，也未运行远程CI。

## 只刷 Dongle，先验收连接

文件：`firmware/build/prospector-dongle-scan-policy-r2.uf2`。
设备页：**T5-09B-SCAN / SOURCE 3C52B1**。

让 Dongle 从设备页双重确认进入 NICENANO，然后：

```bash
cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-dongle-scan-policy-r2.uf2' /Volumes/NICENANO/
```

1. 右侧保持当前固件和供电。确认设备页版本，观察右侧能否自动连接并打字。
2. 保持 Dongle 连接，右侧关闭电源约5秒后重新上电（若接USB供电也需断开），确认自动重连。
3. 前两项通过后，慢速滚球、快速打字、同时操作各约15秒，比较此前的周期性停顿。
   本轮无需完整重采日志。

反馈：自动连接/重连是否通过、滚球是否改善、是否仍丢字。
若连接仍失败，回退 `prospector-dongle-scan-ab.uf2`，保留配对，不重刷右侧。

## 复现与记录

```bash
PROSPECTOR_BUILD_NAME=prospector-dongle-scan-policy-r2 PROSPECTOR_KEYMAP=touch_modes SKIP_WEST_UPDATE=true bash firmware/docs/prospector-touch/scripts/build-touch-only.sh
python3 module/tools/test_scan_startup.py
python3 module/tools/test_scan_policy.py
python3 module/tools/verify_scan_startup.py --elf firmware/build/prospector-dongle-scan-policy-r2/zephyr/zmk.elf --map firmware/build/prospector-dongle-scan-policy-r2/zephyr/zmk.map
```

Native测试需要可用C编译器。构建日志 `firmware/build/reports/t5-09b-dongle-console.log`；
核验记录 `firmware/build/reports/t5-09b-verification.json`。
源与产物校验值见 `releases/T5-09B/prospector-dongle-scan-policy-r2.json`。
修改仍在两仓库本地工作树，远端发布前需要提交模块并更新west pin。

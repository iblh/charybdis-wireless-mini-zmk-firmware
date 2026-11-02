# ATT／报告间隔选择与裸左侧连接测试

## 当前建议：保持800 CPI／ATT3／8ms

ATT3/ATT8表示可用的ATT发送缓冲数量，不能当作蓝牙速度档或报告率。
固定源码 `zephyr/subsys/bluetooth/host/Kconfig.gatt` 和
[Zephyr Host文档](https://docs.zephyrproject.org/latest/services/connectivity/bluetooth/bluetooth-le-host.html)
均将其用于发送缓冲资源管理。

此前ATT8将分配等待均值从0.771ms降到0.036ms，但Dongle RX的30–50ms间隔占比
为ATT3 9.24%、ATT8 9.72%，未显示端到端节奏改善。它缓解前段分配等待，不能消除后段瓶颈。
这个对照是在旧扫描策略下进行；r2和双连接下ATT8的效果尚未重新测试，不能断言它永远更差。
当前没有足够收益支持改变已经明显改善的ATT3基线。
数据与计时边界见 [ATT3/ATT8结果](22-att3-att8-results.md)。

8ms/12ms是PMW完整运动报告的最短间隔；理论频率上限分别约125Hz和83Hz，
不代表传感器采样率、实际BLE接收率或显示器刷新率。12ms减少可用报告机会和发送负载，
也会延长位移合并等待，不天然比8ms顺滑。当前没有修复扫描后的严格8/12对照证据，先保留8ms。
需要比较时，两版必须保留相同的方向校正、位移累计修复、CPI、日志及Dongle扫描策略；
不能拿旧正常12ms版和新版8ms直接归因于间隔差别。

后续优先级：本次双连接观察 → 关闭右侧详细诊断的日用版 → 若仍有可见颗粒感，
再单变量测量7.5ms连接节奏与报告调度、或评估减少分轴通知的协议开销。
XY合帧需要两端协议/兼容与按键公平性验证，目前未实现。
不通过不断扩大缓冲或默认滤波掩盖尚未定位的问题。

## 为何裸主控可以用

目标是用户确认的同款Pro Micro nRF52840 / nice!nano v2兼容主控。
正常左侧固件无需轨迹球或显示器；矩阵列使用内部下拉，没有焊接开关时不会主动生成按键动作。
主控经USB供电即可保留真实split服务、绑定和BLE连接。
它不会作为单独蓝牙键盘与电脑配对，中央仍是现有Dongle。
角色说明见 [ZMK split文档](https://zmk.dev/docs/features/split-keyboards)。

本次只编译左侧，未改其运行配置或引脚。构建脚本新增
`PROSPECTOR_PERIPHERAL_SIDE=left|right|both`（默认both），直接使用只读sibling module，
不再依赖旧West模块镜像。生成的左侧UF2与原正常左侧UF2逐字节相同，未覆盖旧文件。

文件：`firmware/build/prospector-left-link-test.uf2`，**只刷新裸主控**。
Build PASS；FLASH189536B、静态RAM37808B；UF2 `0x26000–0x54500`，限额余363264B。
确认左侧shield、BLE peripheral、ATT3、无PMW、无开机清绑定/重置；硬件连接待用户验证。
元数据见 `releases/T5-10L/`。

## 刷写与最短观察

1. 保持Dongle的r2和右侧当前固件不变。先只让右侧在线，以相同主机设置慢速滚球约20秒。
2. 新裸主控接USB；若有Reset按钮，快速双击；否则快速短接RST与GND两次，进入NICENANO。
   只让这块主控进入刷机盘，避免刷错目标。
3. 复制：

   ```bash
   cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-left-link-test.uf2' /Volumes/NICENANO/
   ```

4. 自动重启后继续经USB供电，无需接按键或电池，也无需在macOS蓝牙列表配对。
   可用电脑的另一USB口或USB充电器；裸板放在不导电表面，不碰矩阵引脚。
5. 等待约60秒，Dongle上滑设备页，确认 **K1 ON、K2 ON**，不要仅根据电量数字判断连接。
6. 双连接稳定后，用右侧重复约20秒慢速滚球/快速打字，再拔掉左侧USB恢复单连接，重复相同动作。
   不要求本轮重新完整采日志；记录单侧/双侧/再次单侧的差别，以及是否断线或丢字。

r2策略在两连接已建立时停止扫描；退回单侧时恢复5ms/200ms低占空比搜索。
第二个BLE连接本身也占射频时隙，因此此测试不是严格的“只改变扫描”单变量实验。
它能检验真实双连接场景下右侧手感，不能证明双侧同时大量打字、左侧矩阵或电池已验收。

## 全新主控与旧绑定槽

用户确认这是全新的主控，不是原左侧那块。BLE绑定按硬件身份存储，重新刷同一UF2不会继承旧身份。
固定ZMK源码 `ble.c:zmk_ble_put_peripheral_addr()` 只接纳已有身份或空的地址槽；
两槽都已绑定时，新身份无法加入，即使旧左侧当前不在线。

若60秒后仍只有一侧ON，先保留现象并反馈K1/K2状态。不要反复重刷右侧、不要运行settings_reset，
也不要清除全部绑定。应先核实旧左侧槽是否仍占用；若确需解除旧左侧绑定，需要单独准备并获得批准，
保留已工作的右侧配对。本次固件没有此清除动作，不能保证空闲连接名额等同于空闲绑定名额。

## 复现

```bash
PROSPECTOR_PERIPHERAL_SIDE=left bash firmware/docs/prospector-touch/scripts/build-touch-peripherals.sh
```

仅使用本地固定依赖，不执行west update；构建日志在
`firmware/build/reports/left-link-test-build.log` 与 `firmware/build/prospector-peripheral-left-build.log`。

# KeyBeacon与Prospector USB Dongle：接入评估

研究日期：2026-11-12。本轮仅做源码评估，不把尚未开发/构建/实测的遥测功能放进当前候选包。

## 核对的上游

- [KeyBeacon app/协议](https://github.com/ykiewang/keybeacon/tree/4c80e3dce9b24ab5d0bbfc84983adc9c91d77663)：macOS菜单栏/悬浮窗、Windows托盘/悬浮窗，当前协议KBP1.2。
- [zmk-keybeacon v1.2.0](https://github.com/ykiewang/zmk-keybeacon/tree/66f2486ce3d42d56b7a7853f57f988052a35f98b)：固定commit66f2486c；MIT。
- [固件入口](https://github.com/ykiewang/zmk-keybeacon/blob/v1.2.0/GETTING-STARTED.md)、[Kconfig](https://github.com/ykiewang/zmk-keybeacon/blob/v1.2.0/Kconfig.keybeacon)。

源码核对，不把README中的路线图当已实现功能：

- `app/macos/Sources/BleWidgetCore/BLEClient.swift`使用CoreBluetooth，枚举已连接HID/KBP服务并读取/订阅GATT；没有USB串口或USB HID状态传输实现。
- `keybeacon.c`提供AA1层/显式修饰键、AA2连接/profile/输出、AA3电量、AA4每BLE主机身份。连接变化/状态变化时推送。
- `compatibility.yaml`已列出ZMK `4dd95d7`，恰好是本项目的固定ZMK。因此没有理由仅为此升级ZMK main。
  这是API兼容声明，不是本项目硬件和三设备结构已实测支持。
- AA2把central本体视为左侧在线，`peripheral_slots[0]`视为右侧；AA3使用central本体电量和slot0外设电量。
  我们的central是无电池Dongle，K1/slot0是右侧、K2/slot1是左侧；直接启用会错误/缺失左侧信息。
- AA1从`zmk_keymap_layer_name()`取最高层。我们还需独立发送MAC-DV/WIN-DV/GAME模式，才能在FN等公共层显示所属模式。
- 上游部分通知直接从ZMK事件监听器调用`bt_gatt_notify()`；若改造成USB，不能简单替换为会等待的USB写操作。

## 三条可行路径

| 路径 | 需要做什么 | 对当前项目的影响 | 判断 |
|---|---|---|---|
| 原版KeyBeacon BLE | 在Dongle加入固定版本模块；额外让电脑通过BLE连接Dongle；修正双外设电量/连接映射和USB输出含义 | 增加主机BLE链路与无线调度，USB切换器不会自动切换此BLE连接；必须做性能A/B | 技术上可研究，但不作为当前默认方案 |
| 保留KeyBeacon界面，增加USB状态源 | Dongle新增独立USB状态接口；fork桌面app增加USB transport，复用界面/状态模型 | 跟随USB切换器；无需增加无线链路；需要固件与macOS/Windows客户端一起开发 | 推荐下一轮原型 |
| 扩展Studio/KeyPeek相关方案 | 先用现有Studio查看键位；实时状态须额外通知协议、客户端支持与接口分离 | 标准Studio USB RPC不等于实时状态接口；共享同一CDC端口会和网页争用 | 查看键位现在可用；实时状态不能仅打开Studio开关完成 |

USB方案不会被未修改的原版KeyBeacon自动识别。需要明确称为兼容界面/USB适配分支，不能宣称原版开箱即用。
也不建议为了复用BLE协议而让电脑改用BLE HID输出；用户仍使用Dongle USB输出。

## 推荐下一轮实现任务（未实现）

1. **T6-01，固定现有基线。** 从v0.1.0-rc1分出USB遥测实验，不同时调整右侧CPI、ATT、8ms或扫描策略。
2. **T6-02，只更新Dongle的USB原型。** 优先研究独立vendor HID接口，避免占用Studio现有CDC端口。
   先验证端点数量/USB枚举与接口共存，再决定是否引入外部Raw HID模块；不预先增加浮动West依赖。
3. **T6-03，定义只读快照。** 版本、序号、输入模式、最高层、活动层掩码、修饰键、左右连接位、左右电量及有效位、USB状态。
   使用`prospector_peripheral_snapshot_get()`与`prospector_peripheral_display_source()`的实际映射；禁止把0%当断线。
   不虚构充电状态，不上传键入文本。模式/层名称使用实际运行态，不复制另一套键位表。
4. **T6-04，保证输入不被遥测阻塞。** 输入回调只更新缓存/提交work；状态合并，最多约20ms发送一次最新快照。
   无变化不持续发送；客户端连接时读取初始快照，断开后停止发送。不能在ZMK输入、BLE或LVGL回调里等USB。
   遥测不采集/转发每个轨迹球运动帧，也不在热路径逐次打印日志。
5. **T6-05，客户端。** KeyBeacon fork中抽象BLE/USB状态源，先macOS菜单栏和紧凑悬浮窗，再Windows。
   复用其语言、固定/穿透设置与界面，只展示有效状态；USB主机身份按当前USB连接解释，不能沿用BLE profile推断。
   保留MIT版权声明；本轮没有复制上游代码。
6. **T6-06，验收门槛。** UF2仍小于0xAD000，RAM/64KB LVGL回归；Studio与状态窗可共存；
   双侧打字/滚球下无队列溢出或输入回退；USB切换/断开后状态正确；新遥测和基线做同参数A/B。
   当前Dongle约29KB可写FLASH余量，USB接口/遥测实现必须先实测资源；不能仅凭估计承诺装得下。

以上是研究结论和可执行任务，不宣称已支持KBP、已构建USB遥测或已验证原版KeyBeacon连接。
当前本轮交付仍是现有UF2的整理/冻结，不要求用户为研究结果重新刷机。

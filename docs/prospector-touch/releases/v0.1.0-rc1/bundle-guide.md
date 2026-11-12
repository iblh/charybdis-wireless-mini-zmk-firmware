# Prospector Touch v0.1.0-rc1

这是当前可工作的固件冻结包，不是全面验收的stable版。已经刷好且左右均连接的用户无需重刷。
三个UF2与之前交付文件逐字节相同，版本继续显示T5-12-USB等原标识。

| 文件 | 唯一目标 |
|---|---|
| dongle.uf2 | 带屏幕的Prospector Dongle |
| left.uf2 | 左键盘 Pro Micro nRF52840 / nice!nano v2兼容板 |
| right.uf2 | 右键盘同款板，PMW3610，800CPI/ATT3/8ms/15° |

右侧保留现有低频诊断/ATT/HCI统计，尚未换成移除插桩的最终日用版。包中不含维护清槽、settings_reset或Bootloader。
不要把左/右文件刷到Dongle。已有配对会保留；仅换新主控时需按身份定向维护，不能靠重刷本包移除旧绑定。

如确需重刷：只让目标板进入NICENANO，使用macOS `cp -X`复制对应UF2；每次核对目标，勿同时挂载多块同名盘。
双侧分别与Dongle连接，不直接彼此或与电脑配对。`SHA256SUMS`记录文件校验值。

## 浏览器查看键位

1. Dongle用数据USB线接电脑。关闭串口日志程序及其他网页，只使用一个客户端。
2. Chrome/Edge打开 https://zmk.studio/ 或 https://srwi.github.io/keypeek/，选择USB及Prospector Touch。
3. 页面提示Device Locked / Unlock To Continue时，保持网页连接。
4. Dongle主页从下往上滑进入DEVICE，点USB EDITOR / UNLOCK；文字变为USB EDITOR / LOCK后回网页继续。
5. 仅查看各层，不改键/保存/重排层。当前未验证任意层重排与模式/轨迹球逻辑的兼容性。

锁提示说明服务在响应，并不表示刷机失败。解锁是触屏入口，不需要再添加键位或重新刷机。
若仍锁定，请记录设备页版本/USB EDITOR文字及网页错误；不要重置BLE配对。

本版没有KeyBeacon实时桌面状态支持。

源码、资源校验与验收边界：
https://github.com/iblh/charybdis-wireless-mini-zmk-firmware/tree/feat/touch-no-sensor/docs/prospector-touch/releases/v0.1.0-rc1

# T5-10L：裸主控的左侧BLE连接测试

文件：`firmware/build/prospector-left-link-test.uf2`，只刷同款nice!nano v2兼容的裸左侧主控。
这是正常左侧peripheral固件，和原 `prospector-touch-left-peripheral.uf2` 逐字节一致。
SHA-256：`a08fafd75ea6732cebd80596c7761928c449d4beca0c6de9e91f320c60fc6a9f`。

左侧单目标Build、角色/无PMW/无清绑定配置及UF2检查通过；FLASH189536B、静态RAM37808B。
UF2末端0x54500，旧Bootloader限额余363264B。实机连接待验收。
Dongle r2和右侧800 CPI／ATT3／8ms文件哈希保持原值，无需重刷。

全新主控需要空闲的绑定地址槽；旧左侧已绑定时不能仅凭另一侧离线就自动替换。
不在本固件中清除配对。[参数结论、刷写、连接观察与旧绑定处理](../../docs/29-parameters-and-bare-left-test.md)。

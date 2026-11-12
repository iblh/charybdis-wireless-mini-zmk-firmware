# T5-11：定向旧左侧绑定维护候选

仅刷Dongle：`firmware/build/prospector-dongle-left-slot-recovery.uf2`。
标识 **T5-11-LEFT / SOURCE A31BE3**。
SHA-256：`b0f990d98a51f9003505262cc13af96f8e5f11b4330a7b946e61e8e1d8a89f1f`。

用户已明确授权检查/处理旧左侧槽，保留右侧配对。固件在设备上核实存储；
只在保护条件满足时清理K2的旧地址及对应bond，检查K1地址与持久化密钥未变。
持久化一次性记录，后续重启不会再次清理新左侧；错误时不开放split发现。

Build、实际恢复C/central hook/key编码native、LVGL UI、ELF和UF2检查PASS。
FLASH503328B、静态RAM216578B、UF2末端0xA0F00，旧Bootloader限制余49408B。
普通构建默认不包含维护，应用payload与已验收r2除SOURCE/构建时间外一致。
用户已确认 **LEFT CLEARED、K1 ON、K2 ON**。仅连接验收，完整左侧矩阵未测；没有自动刷写。
用户之后再次换板时必须使用 T5-12 的独立 v2 维护事务，旧版不会重新清槽。

右侧、新左侧固件均不改；日用r2回退文件原路径和SHA保持原值。
[刷写、结果标签、保护机制及回退](../../docs/30-left-slot-recovery.md)。

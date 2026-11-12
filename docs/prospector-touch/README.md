# Prospector Touch Edition

日常只需阅读这四份文档：

| 文档 | 用途 |
|---|---|
| 本页 | 项目入口和目录 |
| [USER-GUIDE.md](USER-GUIDE.md) | 当前固件、刷写/配对、触屏、输入模式、鼠标操作、Studio解锁 |
| [DEVELOPMENT.md](DEVELOPMENT.md) | 两个仓库、硬件、固定依赖、构建与测试、文件保留规则 |
| [STATUS.md](STATUS.md) | 已验证/待验证事项、当前版本、下一步与本轮整理结果 |

当前是v0.1.0-rc1冻结包。用户已确认T5-12刷入后左右均可连接，现有配置不需要因为整理重刷。
KeyBeacon暂不开发；当前固件未加入实时桌面遥测。

```text
prospector-pro/
  AGENTS.md                         本地工作约定
  firmware/
    config/                         硬件、键位和固定依赖
    docs/prospector-touch/           本文档入口
      scripts/                      构建、采集和核验工具
      releases/                     版本清单和界面预览
      artifacts/                    原成功CI证据
      archive/history/              原交接README及01–34历史文档
      archive/reference/            旧参考代码，不能覆盖现有源码
    build/                          仅当前UF2、一个回退和RC包
    .local-artifacts/               本地原始日志/压缩证据，Git忽略
  module/                           UI、驱动、行为和主机测试
  pcb/                              用户PCB资料
```

原`prospector-pro-handoff`是指向本文档目录的快捷链接，已移除；以后使用正式路径
`firmware/docs/prospector-touch/`。原始历史仍可在 [归档入口](archive/history/README.md) 查阅。
历史中的状态/路径对应记录当时，不代表当前固件；当前状态以[STATUS](STATUS.md)和版本清单为准。

[RC1版本清单](releases/v0.1.0-rc1/README.md) ·
[firmware仓库](https://github.com/iblh/charybdis-wireless-mini-zmk-firmware/tree/feat/touch-no-sensor) ·
[module仓库](https://github.com/iblh/prospector-zmk-module/tree/feat/touch-no-sensor)

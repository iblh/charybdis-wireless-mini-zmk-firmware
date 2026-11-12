# T5-05：慢速精细移动对照与备用帧间隔诊断

q64 双端 150 秒日志未记录到中央队列丢事件、USB 发送错误或明显长等待。
用户反馈按键可用，轨迹球剩余问题明确为慢速精细移动的颗粒感。
本轮先比较 1600 CPI，保留 Dongle q64；不要求同时更换两端。
详见 [双端分析与操作](../../archive/history/docs/18-trackball-fine-motion.md)。

| 文件（`firmware/build/`） | 刷写目标 | FLASH / 静态 RAM | SHA-256 |
|---|---|---|---|
| `prospector-right-profile-8ms-angle15-cpi1600.uf2` | **右键盘，先测试这一份** | 238392 / 74544 B | `c09e00c64bf2752856d1eeb676c7a5b0f9930f2d61c5b0e362a8c819161d83ab` |
| `prospector-dongle-pipeline-q64-cadence.uf2` | Dongle，备用，暂不要求刷 | 541664 / 222282 B | `8a857e1d02c95104f95f7cb539725630095967db64d53758d9accba160715be6` |

两份均为 Build/native/UF2 PASS，**实机待验收**，未自动刷写。
右侧 UF2 地址 `0x26000–0x60400`，旧 Bootloader 限额余 314368B。
备用 Dongle 地址 `0x26000–0xAA400`，余 11264B；SOURCE ID `9AF40F`，标签 `T5-05-TIMING`。

1600 CPI 版与原 800 CPI / 8ms / 15°：

- 有效 Kconfig 完全相同；运行 driver、光学统计、旋转数学与角度系数源文件完全相同。
- 实际编译设备树仅 `cpi = <800>` 改为 `<1600>`；GPIO、SPI、轴配置、force-awake、键位不变。
- 旧 800 CPI 回退 UF2 SHA 仍为 `d31457c065fbf57adbf7e435987a49a23bca8bb5882c692bd70d7ba6bc83ab61`。
- 当前 Dongle q64 UF2 SHA 仍为 `79e7c27cb6bee801e701183b5037884530cfa2a8a807e52d0bc4c5a691418f46`。
- 不改配对、不改充电、不改 Bootloader，不引入移动平均/插值。

复现右侧：

```bash
PROSPECTOR_POINT_INTERVAL_MS=8 PROSPECTOR_POINT_ANGLE_DEG=15 PROSPECTOR_POINT_CPI=1600 bash firmware/docs/prospector-touch/scripts/build-right-profile.sh
```

备用 Dongle 的额外帧间隔统计默认为关闭，只有以下构建启用：

```bash
PROSPECTOR_PIPE_QUEUE=64 PROSPECTOR_PIPE_CADENCE=true bash firmware/docs/prospector-touch/scripts/build-pipeline.sh
```

本地验证：

- 两份 Docker/West 单目标构建、有效配置/设备树核对、UF2 地址检查：PASS。
- 原有队列/USB 失败注入、成功 USB 鼠标提交才增加帧计数：PASS。
- 实际 cadence C 的全部桶边界、两个统计点独立、跨窗口延续、周期计数和 uptime 回绕：PASS。
- 实际 PMW 报告/旋转 C 的 15°/40°、8ms/12ms、小数余量与迟到采样：PASS。
- 工作树 diff whitespace 检查及构建脚本语法：PASS。

JSON 记录实际源码、构建配置与产物摘要。构建通过不代表颗粒感已修复。

后续实测：用户已刷 1600 CPI 并调低主机速度，慢速颗粒感仍存在，未验收为改善。
现启用已构建的备用 cadence Dongle，保持右侧 1600 CPI；具体步骤见
[帧间隔采集流程](../../archive/history/docs/19-cadence-test-protocol.md)。

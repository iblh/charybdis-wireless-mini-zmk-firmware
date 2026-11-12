# T5-03：右侧轨迹球方向与流畅度诊断候选

2026-10-31，本地构建/测试通过，**两份均待实机验收**。

- `prospector-right-profile-12ms-angle15.uf2`：右 BLE 外设，顺时针 15° 校正、保留原
  12ms 节流，加入延迟样本下的缓存保留修复和每两秒的诊断统计。
- `prospector-right-profile-8ms-angle15.uf2`：相同代码和设置，仅最短报告间隔改为 8ms。

两份均 FLASH 238,392 B、静态 RAM 74,544 B；UF2 范围 `0x26000–0x60400`，
距旧 Bootloader 上限余 314,368 B。JSON 保存最终哈希、源校验与依赖。

实际旋转/统计 C、实际驱动报告函数的 native 测试、串口采集器伪终端测试、
Docker/West 右侧单目标和 UF2 guard 已通过。尚无实机方向或连续运动验收结果。
原 West driver 和正常右侧 UF2 均保留，左侧和 Dongle 无需随此候选刷写。

操作、参数含义、比较边界、回退与当前鼠标键位见
[完整测试指南](../../archive/history/docs/16-trackball-calibration-and-performance.md)。

这是临时诊断候选，不能直接作为最终电池续航/游戏延迟结论。稳定后再制作关闭
统计的正常版。未增加中键绑定、自动鼠标层或滚动锁定，未清除蓝牙绑定。

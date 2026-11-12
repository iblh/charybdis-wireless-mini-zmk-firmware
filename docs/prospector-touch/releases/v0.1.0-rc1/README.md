# Prospector Touch v0.1.0-rc1

2026-11-12冻结当前UF2，准备GitHub **draft prerelease**；不是全面验收的stable，不要求现有用户重刷。
使用原T5-12 Dongle、正常左侧与800CPI/ATT3/8ms右侧；版本、SOURCE和SHA保留。
不含维护清槽、settings_reset、Bootloader或KeyBeacon实验。

| 角色 | 包内文件 | 原本地文件 | SHA-256 |
|---|---|---|---|
| Dongle | dongle.uf2 | prospector-dongle-controls-usb.uf2 | 35357d55b43cf1f672383f56f135170d09c878382713d9695d667adffb57a0a6 |
| 左侧 | left.uf2 | prospector-left-link-test.uf2 | a08fafd75ea6732cebd80596c7761928c449d4beca0c6de9e91f320c60fc6a9f |
| 右侧 | right.uf2 | prospector-right-hci-cpi800-att3.uf2 | c471b19320f3ef6f4f5a26327a722d461a234f319e9ae7e6f6285b43f6082246 |

右侧仍含诊断插桩，因此不把这个包称为最终无诊断日用版。
发布草稿tag使用`touch-v0.1.0-rc1`，避免触发原v*标签的完整构建矩阵。
二进制ZIP上传GitHub候选草稿；源码仓库只保留说明和清单，生成包在Git忽略的build目录。

## 验证与实机反馈

- 用户确认全部刷好、没有问题、左右均能连接。
- 用户确认USB能连接到Studio/KeyPeek并收到锁提示；服务响应通过，解锁后读取键位仍待确认。
  正确顺序：**先让网页连接并显示Locked，再上滑Dongle设备页点USB EDITOR / UNLOCK**。
- 固定新module提交后的独立Build、UF2限额和ELF顺序PASS。
  应用payload除SOURCE/时间共11字节外与已验收Dongle相同，有效config/DTS逐字节一致。
  [源码核对](published-source-check.json)；固定module `1345b3e91e23b8686f2b8b3e121515c6b3e52e84`。
- 原32位/64KB LVGL实际UI测试：报告峰值36448B，120次页面开关无保留增长、120次三布局切换PASS。
- 当前native：设备服务、完整mod-morph/快捷键、扫描策略/启动、两代定向维护故障注入和外设状态PASS。
- 未运行新远程CI，未把本地PASS写成CI PASS；未自动刷写硬件。

## 转为stable之前

1. 完成网页解锁、查看九层键位；不编辑/重排层。
2. 双侧各自断电重连，连续打字/滚球、MAC-DV/WIN-DV/GAME快捷键及鼠标点击/滚动/拖拽。
3. T5-12的5分钟休眠/触摸唤醒，以及macOS/Windows的USB切换与主机睡眠唤醒。
4. 将右侧方向校正、分数累计、迟到采样保留、8ms门限与ATT/HCI统计分离，生成无诊断候选，做单变量回归。
5. 通过上述验收后再正式发布；KeyBeacon/USB遥测另开实验，不混入收敛。

## 打包与目录

从工作区根目录：

```bash
python3 firmware/docs/prospector-touch/scripts/package-release.py firmware/docs/prospector-touch/releases/v0.1.0-rc1/manifest.json
```

输出`firmware/build/releases/v0.1.0-rc1/prospector-touch-v0.1.0-rc1.zip`和`.zip.sha256`。
脚本核对三个原UF2的精确SHA、向量及Bootloader范围，并回读ZIP所有文件。
清单见 [manifest](manifest.json)，独立操作说明见 [包内指南](bundle-guide.md)。

[KeyBeacon/USB状态窗方案](../../docs/33-keybeacon-assessment.md) ·
[本地整理记录](../../docs/34-cleanup-2026-11-12.md)。

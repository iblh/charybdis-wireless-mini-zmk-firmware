# 使用指南

## 当前固件

已经刷好且左右均连接时无需再刷。`firmware/build/`保留：

| 文件 | 唯一目标 / 用途 |
|---|---|
| `prospector-dongle-controls-usb.uf2` | 当前屏幕Dongle；T5-12-USB / SOURCE A9EA70 |
| `prospector-left-link-test.uf2` | 正常左侧外设；已连接实际按键矩阵时也用它 |
| `prospector-right-hci-cpi800-att3.uf2` | 当前右侧外设；800CPI / ATT3 / 8ms / 顺时针15°；仍含诊断 |
| `prospector-dongle-scan-policy-r2.uf2` | 旧版已验收Dongle回退，无新UI/USB Studio |

RC包：`firmware/build/releases/v0.1.0-rc1/prospector-touch-v0.1.0-rc1.zip`，
含`dongle.uf2 / left.uf2 / right.uf2`、说明与SHA256SUMS，不含清配对或Bootloader。
[完整版本清单](releases/v0.1.0-rc1/README.md)。

## 刷写和配对

1. 一次只让目标主控进入NICENANO，避免多块同名盘刷错。
2. 左右主控快速双击Reset；Dongle可上滑DEVICE → FLASH → 再长按HOLD 2S。
3. macOS用`cp -X`复制该角色UF2，例如只刷Dongle：

   ```bash
   cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-dongle-controls-usb.uf2' /Volumes/NICENANO/
   ```

4. 重启后Dongle经USB接电脑，左右供电，自动通过BLE连接Dongle；不在系统蓝牙列表配对。
   当前 **K1=右侧、K2=左侧**，双侧正常时均ON。左右之间不直接配对。
5. 如确需确认刷入内容，进入NICENANO后只读核对：

   ```bash
   python3 firmware/docs/prospector-touch/scripts/check-flashed-dongle.py
   ```

磁盘立即消失并重启时，cp可能报告Device not configured，先检查版本/读回，不能只凭退出状态断言失败。
换全新主控会改变BLE身份；旧绑定可能占槽。不要全局settings_reset、重刷右侧或重复刷旧维护文件。
前两次左侧更换已处理，v1/v2维护记录都是一次性的；将来再换板需另做保留右侧的定向维护。

## 触屏

- 左右滑：循环Classic / Field / Operator三种状态外观。
- 下滑：亮度页，手动10–100%，CLOSE返回。
- 上滑：DEVICE，查看版本、USB、K1/K2；INPUT MODE选择输入模式。
- FLASH：先进入确认页，再独立长按HOLD 2S；不会因为一次误触直接刷机。
- 默认五分钟空闲熄屏；旧版休眠/触摸唤醒已实测，新T5-12变体仍需单独回归。

## Studio / KeyPeek查看键位

1. 用数据USB线把**Dongle**接电脑，关闭screen、串口日志和其他占用设备的网页。
2. Chrome/Edge打开 [ZMK Studio](https://zmk.studio/) 或 [KeyPeek](https://srwi.github.io/keypeek/)，
   选择USB及Prospector Touch；同一时间只用一个客户端。
3. 网页显示Device Locked / Unlock To Continue时保持连接，Dongle上滑DEVICE，点
   **USB EDITOR / UNLOCK**。按钮变为**USB EDITOR / LOCK**后回网页继续。
4. 手动选择MAC-DV、WIN-DV、GAME、NUM、NAV、SYM、FN、SLOW、SCROLL层查看。

锁提示说明服务在响应，不需要重刷。标准解锁也允许编辑，本阶段只查看，不改键/保存/删除或重排层。
`QUOTE / Q`等名称前项是Dvorak输出，后项是QWERTY快捷键分支。当前无桌面浮窗自动跟随层的功能。

## 三种输入模式

屏幕外观和输入模式彼此独立。Mac/Windows系统输入布局都保持美式QWERTY，由键盘输出Dvorak。
使用USB切换器后须手动选择对应输入模式；启动默认MAC-DV，不保存模式。

| 模式 | 字母输出 | 临时QWERTY快捷键条件 |
|---|---|---|
| MAC-DV | Dvorak | 按住左/右Command或Ctrl |
| WIN-DV | Dvorak | 按住左/右Ctrl |
| GAME | QWERTY | 始终QWERTY，主要字母/拇指直接输出 |

模式在所有实体键和HID报告释放、安静至少350ms后切换；RELEASE ALL KEYS表示仍在等待。

```text
MAC-DV / WIN-DV:
 ESC    '    ,    .    P    Y   |   F    G    C    R    L   BSPC
 TAB    A    O    E    U    I   |   D    H    T    N    S   ENTER
 SHIFT  ;    Q    J    K    X   |   B    M    W    V    Z   SHIFT

GAME / 快捷键字母分支:
 ESC    Q    W    E    R    T   |   Y    U    I    O    P   BSPC
 TAB    A    S    D    F    G   |   H    J    K    L    ;   ENTER
 SHIFT  Z    X    C    V    B   |   N    M    ,    .    /   SHIFT
```

打字模式Home-row mods：

| 位置 | MAC-DV按住 | WIN-DV按住 |
|---|---|---|
| 左A / O / E / U | Command / Alt / Shift / Ctrl | Ctrl / Alt / Shift / Win |
| 右H / T / N / S | Ctrl / Shift / Alt / Command | Win / Shift / Alt / Ctrl |

点按仍输出字符。初次熟悉可先按住约300ms，看屏幕修饰键亮起后再按快捷键。

| 拇指位置 | 打字模式点按 / 按住 | GAME |
|---|---|---|
| 左外 | Esc / FN | 左Ctrl |
| 左中 | 鼠标左键，可直接拖拽 | 左Alt |
| 左内 | Backspace / NUM | Space |
| 右内 | Enter / SYM | 鼠标左键 |
| 右外 | Space / NAV | 按住FN |

FN：第一行为F1–F12；第二行左侧前三键选择MAC/WIN/GAME，后有BL-/BL+，右侧是媒体/音量；
第三行是数字1–0。NUM提供数字，NAV提供导航和编辑快捷键，SYM提供符号。

## 鼠标、滚动和拖拽

- MAC-DV/WIN-DV：左中拇指是鼠标左键，按住配合滚球拖拽。
- 按住左外拇指进入FN，再按右内拇指是鼠标右键。
- FN＋左中拇指＋滚球：页面滚动；FN＋左内拇指＋滚球：慢速精细移动。
- GAME：右内拇指直接是鼠标左键，右外拇指是FN入口；同样可在FN内使用右键/滚动/慢速。

右侧参数先保持800CPI / ATT3 / 8ms；当前没有证据要求改ATT8或12ms。
完整快捷键、鼠标键/滚动/拖拽仍需逐项实机验收，不能由键位表或构建通过代替。

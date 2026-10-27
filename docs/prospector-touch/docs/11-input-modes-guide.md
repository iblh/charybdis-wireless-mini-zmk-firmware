# 三种输入模式：使用和验收

本轮新增专用 `firmware/config/keymaps/touch_modes.keymap`，保留原 QWERTY 文件和 T4-01 固件。
新固件的本地验证和最终体积见文档 06；真实键盘行为在用户验收前一律标为待验证。

## 切换方式

主屏上滑 → DEVICE → MODE 行 → MAC-DV / WIN-DV / GAME。
绿色为当前模式；请求尚未生效时为琥珀色，并提示 RELEASE ALL KEYS。
所有实体键松开且 HID 键盘、媒体、鼠标按钮报告为空，等待至少 350ms 后才切换。
按住 Fn 在键盘上选择模式，也要先松开 Fn；后提出的请求取代前一个，选择当前模式可取消等待。
BACK 只返回设备页，不撤销已经选择的模式。启动默认 MAC-DV，本轮不保存模式。

两台电脑的系统输入布局保持 **QWERTY（美式）**。USB 切换器不会自动替你切换模式。
屏幕的 Classic / Field / Operator 外观与输入模式完全独立。

| 模式 | 普通输出 | 临时 QWERTY 条件 |
|---|---|---|
| MAC-DV | Dvorak | 左/右 Command 或 Ctrl 按住 |
| WIN-DV | Dvorak | 左/右 Ctrl 按住；Win、Alt、Shift 单独按住不触发 |
| GAME | QWERTY | 一直 QWERTY，字母和主要拇指键不经过长按/双击判定 |

临时变换覆盖字母和对应标点位置，保留触发修饰键与 Shift/Alt。
按下时决定字母分支，松开时释放同一个键，不因先松 Command/Ctrl 而改成释放另一个字符。

## 基础键位（左右各 3×6，加 3+2 个拇指键）

```text
MAC-DV / WIN-DV：
 ESC    '    ,    .    P    Y   |   F    G    C    R    L   BSPC
 TAB    A    O    E    U    I   |   D    H    T    N    S   ENTER
 SHIFT  ;    Q    J    K    X   |   B    M    W    V    Z   SHIFT

GAME / 临时快捷键字母分支：
 ESC    Q    W    E    R    T   |   Y    U    I    O    P   BSPC
 TAB    A    S    D    F    G   |   H    J    K    L    ;   ENTER
 SHIFT  Z    X    C    V    B   |   N    M    ,    .    /   SHIFT
```

打字模式 Home-row mods：

| 手指位置 | MAC-DV 按住 | WIN-DV 按住 |
|---|---|---|
| 左 A / O / E / U | Command / Alt / Shift / Ctrl | Ctrl / Alt / Shift / Win |
| 右 H / T / N / S | Ctrl / Shift / Alt / Command | Win / Shift / Alt / Ctrl |

这些键点按输出 Dvorak 字符。保留原架构的 balanced 280ms 判定、175ms quick-tap、150ms prior-idle 和异手触发。
初次验收先按住修饰键约 300ms，确认屏幕修饰键亮起后再按字母；之后再测试自然输入速度。
字母快速连打、同手滚动和长按时机仍需根据实际手感调校，不能由自动测试代替。

| 拇指位置 | 打字模式点按 / 按住 | GAME 直接输出 |
|---|---|---|
| 左外 | Esc / FN | 左 Ctrl |
| 左中 | 鼠标左键，可直接拖拽 | 左 Alt |
| 左内 | Backspace / NUM | Space |
| 右内 | Enter / SYM | 鼠标左键 |
| 右外 | Space / NAV | 按住 FN |

拇指层键判定 200ms。滚动、慢速通过 FN + 对应拇指键进入，避免鼠标左键本身再被长按判定影响拖拽。
数字、符号和导航层可由打字模式拇指进入；GAME 用 FN 的第三行输入数字。

## FN 层（三种模式共用）

```text
 F1    F2    F3    F4    F5    F6   |   F7    F8    F9    F10   F11   F12
 MAC   WIN   GAME  --    BL-   BL+  |   PREV  PLAY  NEXT  MUTE  VOL-  VOL+
 SHIFT 1     2     3     4     5    |   6     7     8     9     0     SHIFT
                 原键  SCROLL SLOW |   鼠标右键  原键
```

打字模式按住左外拇指进入 FN；GAME 按住右外拇指进入 FN。
MAC/WIN/GAME 为第二行左侧前三键；提出请求后先松开所有键。
FN + 左中拇指 + 轨迹球滚动；FN + 左内拇指 + 轨迹球慢速移动。
没有继承原作者的终端宏、BT_CLR 组合、个性化 tap-dance 或隐藏模式组合。

## NUM / NAV / SYM

- NUM：右侧 7–9 / 4–6 / 1–3，右内拇指 0；右侧还包含加减乘除、等号和小数点。
- NAV：右侧 Home、End、Page Up/Down，以及 Left/Down/Up/Right；左侧 Undo/Cut/Copy/Paste/Redo/Select All。
  编辑动作用 MAC-DV 的 Command、WIN-DV/GAME 的 Ctrl；终端 Ctrl 行为不做全局替换。
- SYM：第一行 `! @ # $ % ^ & * ( )`；第二行含反引号、`< > = _ - + [ ]` 和反斜杠；
  第三行含波浪线、单双引号、分号、冒号、管道、斜杠、花括号与问号。

状态页显示 MAC-DV / WIN-DV / GAME；临时层使用 M/NUM、W/NAV、G/FN 等前缀，保留当前模式线索。
MAC 使用 CMD/OPT，WIN/GAME 使用 WIN/ALT。

## 实机验收顺序

1. 上滑打开 MODE，依次选三个模式；检查三种状态外观都同步显示模式和 CMD/OPT、WIN/ALT。
2. MAC-DV / WIN-DV 逐行按字母，与上方 Dvorak 表对照；GAME 逐行对照 QWERTY 表。
3. 在无重要内容的编辑器里核对物理 C/V/X/Z/A/S/W/T 位置的快捷键。
   左右 Ctrl 都测试；Mac 再测左右 Command；加入 Shift/Alt，并分别先松字母、先松修饰键，不能卡键。
4. 按住一个字母或待定 Home-row 键，用触屏选另一模式，应等待松手后才切换。
   通过 FN 切换也应等待 Fn 松开。之后再打字，不能遗留 Ctrl/Command/临时层。
5. GAME 测试 W 长按、W+A、Shift+W、Ctrl+W、Space 连按，以及 FN 的数字、F1–F12、媒体键。
6. 测试鼠标左键拖拽、FN+SCROLL、FN+SLOW；5 分钟熄屏后按键/轨迹球唤醒，确认首键不丢。
7. USB 切换两台电脑时手动匹配模式；边打字边滑屏/调光，观察漏键、卡键、断连。

只改 Dongle 键位通常不需要重刷已经兼容并配对的左右 BLE 外设。
若左右尚未刷入并配对，应先核对固件角色、split 协议和 41 个位置映射，不能把“模式页能切换”视为键盘验收。
回退文件为 `firmware/build/prospector-touch-device-page-qwerty.uf2`。

## 首次刷入和自动配对（左右尚未刷入）

用户确认：左右均为 Pro Micro nRF52840 / nice!nano v2 兼容板，尚未刷固件。
本轮另外构建同一套本地 ZMK/Zephyr/PMW3610 依赖的两只 BLE 外设。外设沿用原 QWERTY
配置作 Devicetree 构建输入，但按键位置由 Dongle 解释，因此仍支持 Dongle 的全部三种模式。
这些是正常外设固件，不是 settings_reset，也不是左右直接连接电脑的 BT central 固件。

1. 先只接 Dongle，通过 DEVICE → FLASH → HOLD 2S 进入 NICENANO，复制
   `firmware/build/prospector-touch-input-modes.uf2`。重启后可先测试 MODE 页切换。
2. 暂时拔下 Dongle，一次只接一块需要刷写的主控，避免同名 NICENANO 磁盘造成目标混淆。
   让**左键盘主控**进入 UF2 磁盘，确认此时接的是左侧，再复制
   `firmware/build/prospector-touch-left-peripheral.uf2`。复制后等待自动重启，再断开 USB。
3. 同样单独接**右键盘主控**，复制 `firmware/build/prospector-touch-right-peripheral.uf2`。
   本项目右侧配置包含 PMW3610 轨迹球；左右文件不要互换，也不要复制到 Dongle。
4. Dongle 插在电脑 USB 上；先给左键盘供电，观察 DEVICE 中 K1/K2 哪一个变 ON；
   再给右键盘供电，观察另一个是否变 ON。首次无旧绑定时应自动建立内部 BLE 连接，
   无需在 macOS/Windows 蓝牙设置中配对这只 USB Dongle。
   两个槽位的左右身份以这一步实际观察为准，不预先假定 K1 就是左侧。
5. 打开空白编辑器，选 MAC-DV 或 WIN-DV，以物理 QWERTY 位置依次点按：
   `Q W E R T Y U I O P`，预期字符为 `' , . p y f g c r l`（此处空格只用于分隔）；
   选 GAME 后同样位置应输出 `q w e r t y u i o p`。
6. 两侧 ON、能正常输出后，再按上方完整验收清单测快捷键、游戏与轨迹球。

如果键盘主控在 UF2 模式下也显示 NICENANO，可分别使用下列命令，**每条命令对应的那一块板必须单独连接**：

```bash
# Dongle
cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-touch-input-modes.uf2' /Volumes/NICENANO/
# 左键盘（拔下 Dongle 后单独连接左侧）
cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-touch-left-peripheral.uf2' /Volumes/NICENANO/
# 右键盘（拔下左侧后单独连接右侧）
cp -X '/Users/paul/Workspace/Lab/prospector-pro/firmware/build/prospector-touch-right-peripheral.uf2' /Volumes/NICENANO/
```

若没有自动连接，记录 DEVICE 的 K1/K2、两侧供电和重启现象再排查；本轮没有刷写或要求刷写
settings_reset，也没有清除任何配对。UF2 内容与校验值见同名 `.json` 清单。

## 本地复现

```bash
PROSPECTOR_KEYMAP=touch_modes SKIP_WEST_UPDATE=true bash prospector-pro-handoff/scripts/build-touch-only.sh
bash prospector-pro-handoff/scripts/build-touch-peripherals.sh
python3 module/tools/test_input_modes.py
python3 module/tools/test_device_service.py
```

`build-touch-only.sh` 默认仍是原 QWERTY；新模式必须显式指定 `PROSPECTOR_KEYMAP=touch_modes`。
本轮不更新 West 到远端 main；清单记录实际使用的依赖 SHA。

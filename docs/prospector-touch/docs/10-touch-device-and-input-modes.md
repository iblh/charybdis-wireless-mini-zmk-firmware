# 10 — 设备页、触屏刷机与三种输入模式方案

方案日期：2026-10-24。本文保留设计依据，最新实现与验收记录以文档 06、11 为准。

实施进展：第一阶段设备页/双重确认 UF2 入口已写入源码并通过本地构建与 mock 测试，
用户已确认设备页和双重确认进入 NICENANO 均通过，详见 `06-roadmap-and-acceptance.md` 顶部。第二阶段三种输入模式和选择页现已实现并本地测试，真实按键输出尚待配对后的实机验收。
T4-01 设备页版仍显示 QWERTY；T5-01 输入模式版显示真实模式。

## 已确认的需求和基线

- 当前三布局固件 `prospector-touch-three-layouts-qwerty.uf2`：用户确认 Classic / Field / Operator 循环正确，下滑打开亮度正常。
- 不增加布局记忆和休眠时间设置，继续默认 Operator、闲置 5 分钟熄屏。
- 新增上滑设备信息页，提供带双重确认的进入 UF2 刷机模式操作。
- 同一个 Dongle 通过 USB 切换器或拔插连接 Mac / Windows；不需要为三种输入模式创建三个 BLE 主机配置。
- 两台电脑均保持系统 QWERTY，Dvorak 由固件输出。必须支持 Ctrl-QWERTY / Command-QWERTY。
- 输入模式为 MAC-DV、WIN-DV、GAME；屏幕外观仍为 Classic、Field、Operator。二者独立。
- 当前项目的本地构建仍使用 `config/keymaps/qwerty.keymap`，现有 layer 名称和打字行为不能视为已经实现上述三种模式。
- 不更新 Bootloader、不清空配对、不改变已验证引脚。

## 1. 闲置唤醒

现有代码依据：`firmware/zmk/app/src/activity.c` 订阅 `zmk_position_state_changed`，收到按键后切回 ACTIVE；`src/display/main.c` 响应 ACTIVE 恢复屏幕，模块 brightness.c 恢复手动背光。当前配置还启用了 pointing 输入活动处理。USB 供电时，activity.c 不执行其断电休眠路径。

因此预期行为是：键盘和 Dongle 仍连接时，收到真实按键可点亮闲置屏幕，按键继续正常输出。触屏唤醒已经有用户确认；真实键盘唤醒、第一键是否丢失，以及轨迹球唤醒仍需单独测试。电脑本身处于系统休眠时能否被 USB 唤醒，取决于电脑、USB 切换器和系统设置，不能由屏幕唤醒结果推定。

本轮保留 5 分钟超时，不新增设置项。

## 2. 手势和页面结构

| 所在页面 | 操作 | 结果 |
|---|---|---|
| 主状态页 | 左 / 右滑 | 只切换 Classic / Field / Operator 外观 |
| 主状态页 | 下滑 | 打开亮度页 |
| 主状态页 | 上滑 | 打开设备页 |
| 亮度页 | 拖动滑杆 | 调整 10–100% 手动亮度 |
| 亮度页 | CLOSE | 返回原状态页 |
| 设备页 | MODE 行 | 打开 MAC-DV / WIN-DV / GAME 选择页 |
| 设备页 | CLOSE | 返回原状态页 |
| 设备页 | FLASH | 打开刷机确认页，单次点击不重启 |
| 确认页 | CANCEL / 超时 | 取消操作 |
| 确认页 | 连续长按确认 2 秒 | 设置启动模式，重启 Dongle 到 NICENANO |

子页面打开时屏蔽主屏导航手势，避免拖动滑杆时换页。第一版继续使用明确的 CLOSE 返回；不上叠额外手势规则。开页手势结束前不接受新页面上的按钮按下，防止滑动尾端误点。

设备页与确认页各只创建一个共享实例，置于 LVGL 顶层并按需显示，避免在三个状态布局内各复制一份。

### 设备页建议内容（逻辑尺寸 280×240）

```text
                 DEVICE
 FW      TOUCH T4-01
 BUILD   10-24  20:30  AB12CD
 MODE    MAC-DV          CHANGE
 USB     READY
 LEFT    CONNECTED    RIGHT --

       [ CLOSE ]    [ FLASH ]
```

- FW / BUILD：版本号、构建时间和源码内容指纹。当前源码含未提交修改，只展示 Git HEAD 无法区分各次固件；最终 UF2 SHA-256 记录在旁边的构建清单中，不嵌入自身哈希。
- MODE：固件输入模式，由真实键位状态驱动，不猜测当前电脑的操作系统。
- USB：区分主机已配置与仅供电/未就绪；不把插着 USB 等同于 HID 已就绪。
- LEFT / RIGHT：使用实际 split 连接事件，未连接明确显示 `--`。电量仅在收到有效报告后显示，不使用演示值。
- 上面时间和连接状态是示意数据，不是硬件检测结果。
- 页内不展示堆地址、调试宏或配对清除入口。
- 第一阶段尚未实现新 keymap 时，MODE 如实显示现有 QWERTY/BASE；第二阶段才启用三个新模式及 CHANGE，不能提前显示一个没有对应键位行为的 MAC-DV 标签。

### FLASH 的双重确认

1. 用户点击设备页 FLASH，进入专用确认页，提示“键盘连接将暂时断开，重启进入 NICENANO”。
2. 用户松手后重新按住 `HOLD TO FLASH` 两秒；显示进度。提前松开、滑出、CANCEL、离开页面或超时均清除确认状态。

确认页 15 秒无操作自动取消。显示闲置时也取消已武装状态，防止唤醒触摸完成旧操作。第一步和第二步必须来自两次独立接触，不能用一次长按穿透两步。

这是“重启到刷机模式”，不清空任何 settings 或 BLE 配对，也不刷写 Bootloader。若保留普通软件重启，应单独命名为 RESTART，并走独立的确认文案，不能让 RESET 同时表示几种行为。

实现复用现有 ZMK reset 行为所使用的 `bootmode_set(BOOT_MODE_TYPE_BOOTLOADER)` 和重启路径。当前配置为 Adafruit nRF52 启动模式映射（magic 0x57）。设置启动模式失败时留在工作界面并提示失败；不继续重启。LVGL 只负责非阻塞长按计时与提交请求，重启任务由 worker 执行。

实机验收：确认 NICENANO 出现、原有双触 RST–GND 恢复方式仍可用、重新运行应用后配对未丢失。界面只能请求这只 Dongle 进入刷机模式，不让左右键盘一起重启。

## 3. 输入模式

系统端维持 QWERTY。屏幕只是显式选择模式，不向电脑发送不可靠的输入源切换快捷键。

| 模式 | 普通字母 | 临时 QWERTY 条件（本方案默认） | 主要应用快捷键修饰键 |
|---|---|---|---|
| MAC-DV | 固件 Dvorak | 任一侧 Command 或 Ctrl 按住时 | Command |
| WIN-DV | 固件 Dvorak | 任一侧 Ctrl 按住时 | Ctrl |
| GAME | 完整 QWERTY | 始终 QWERTY | 游戏直接接收原始修饰键 |

MAC-DV 中 Ctrl 也使用 QWERTY，覆盖终端常用 Ctrl 快捷键；Windows 的 Win 键暂不触发字母映射变化。若用户已有不同的 Ctrl-QWERTY 习惯，实施前以其原键位文件为准。

Shift / Alt 单独按住不触发 QWERTY。触发修饰键与 Shift/Alt 组合时，仍保持 QWERTY 分支并保留全部修饰键。左右 Ctrl / Command 均应覆盖。

例如物理 QWERTY 的 C 位置在 Dvorak 中是 J：普通按下发送 J；MAC-DV 按 Command 再按该位置发送 Command+C；WIN-DV 按 Ctrl 再按该位置发送 Ctrl+C。

### 建议的 3×6 字母区

下面每侧每行 6 键，5 个拇指键另列。这是待用户确认的基础位置建议，实施时不覆盖用户另有的自定义 Dvorak 键位文件。

```text
MAC-DV / WIN-DV 普通输入：
 ESC    '    ,    .    P    Y       F    G    C    R    L   BSPC
 TAB    A    O    E    U    I       D    H    T    N    S   ENTER
 SHIFT  ;    Q    J    K    X       B    M    W    V    Z   SHIFT

快捷键 QWERTY 分支 / GAME：
 ESC    Q    W    E    R    T       Y    U    I    O    P   BSPC
 TAB    A    S    D    F    G       H    J    K    L    ;   ENTER
 SHIFT  Z    X    C    V    B       N    M    ,    .    /   SHIFT
```

快捷键分支按整个物理字母/标点区映射，不能只替换 C/V/X/Z；否则 Ctrl+W、Command+[ 等习惯仍会不一致。数字、符号层的符号绑定按需要保留自身含义，不在所有层上盲目套用字母变换。

### 修饰键与拇指区

打字模式可沿用当前固件的 home-row hold-tap 架构，具体顺序建议：

- 左手 A/O/E/U：主快捷键修饰键 / Alt / Shift / 次修饰键；I 普通字母。
- 右手 H/T/N/S：次修饰键 / Shift / Alt / 主快捷键修饰键；D 普通字母。
- MAC-DV 主修饰键 Command、次修饰键 Ctrl；WIN-DV 主修饰键 Ctrl、次修饰键 Win。
- 两个边缘 Shift 保留为直接修饰键，方便组合操作与逐步调试。

建议尽量延续现有拇指区域的习惯：

| 拇指键 | 打字模式：点按 / 按住 | GAME：直接按键 |
|---|---|---|
| 左外 | Esc / FN | Left Ctrl |
| 左中 | 鼠标左键 / 滚动模式 | Left Alt |
| 左内 | Backspace / NUM | Space |
| 右内 | Enter / SYM | 鼠标左键 |
| 右外 | Space / NAV | 按住 FN |

该拇指安排是建议，尤其“鼠标键按住滚动”需要处理点击与滚动判定、拖拽需求，不能在没有验收的情况下替换现有轨迹球操作。第一批输入模式固件可先保留用户既有的鼠标、慢速与滚动行为，只增加可达的 FN/模式切换键。

GAME 字母、WASD 和主要拇指键使用直接按键，不继承打字模式的 home-row mods、双击判定或字母组合键。Fn 使用普通 momentary 层。这样长按移动、Shift 冲刺、Ctrl 蹲下不会等待 hold-tap 判断。游戏内是否实际采用物理键码仍须按常玩的游戏验证。

## 4. 功能层

三种输入模式是互斥的基础层。NUM / NAV / SYM / FN 是按住临时进入、松开返回当前基础模式的功能层。现有 SLOW / SCROLL 作为轨迹球辅助层保留，不成为第四种输入模式。

| 功能层 | 建议用途 |
|---|---|
| NUM | 右手数字小键盘式 7–9 / 4–6 / 1–3，0、小数点及四则运算；左手补充编辑键 |
| NAV | 方向、Home/End、Page Up/Down、文本选择与常用编辑快捷键 |
| SYM | 编程符号、括号、引号、反斜杠；优先保证成对符号位置一致 |
| FN | F1–F12、媒体控制、模式切换；游戏模式也可访问 |
| SLOW / SCROLL | 沿用轨迹球慢速与滚动设置，另做兼容性测试 |

FN 建议分区：

```text
F1   F2   F3   F4   F5   F6       F7    F8    F9    F10   F11   F12
MAC  WIN  GAME  --   --   --       PREV  PLAY  NEXT  MUTE  VOL-  VOL+
屏幕截图 / 常用系统操作区          导航或用户自定义区
```

FN 的 MAC / WIN / GAME 直接提出模式切换请求，与设备页 MODE 选择使用同一服务。按键还没松开时先排队，待所有实体键及待定 hold-tap 处理完成后再切换。取消临时层、一次性修饰状态的行为必须明确且不能造成卡 Ctrl/Command。不得仅因为使用 USB 切换器就自动猜 OS。

NAV / FN 中专门的编辑动作按模式生成修饰键，例如 Copy/Paste 为 Mac Command+C/V 或 Windows Ctrl+C/V。终端、tmux 等明确要求 Ctrl 的现有宏不全局替换成 Command。当前仓库附带很多作者个人终端宏，必须逐项审核，不能原样视为用户需求。

模式切换不调用 `BT_SEL`，不改变左右键盘的 BLE 配对。USB 切换器只切换主机，模式由用户触屏或 FN 明确选择。启动默认模式可先设 MAC-DV，不在本轮增加记忆设置；状态页应清楚显示当前模式。

## 5. 实现边界和关键技术点

### Firmware 仓库

- 新增用户专用键位文件，不覆盖现有 qwerty.keymap 和已验证的 UF2。
- 三个完整基础层都覆盖 41 个位置，避免高层透明键意外落回另一 OS 的基础键。
- 重新明确 layer ID；当前 combos、tap-dance、hold-tap、轨迹球层引用的数字必须统一审核。
- 字母/标点的快捷键转换优先用当前 ZMK `mod-morph` 机制。设置对应 `mods` 和相同触发位的 `keep-mods`，确保真的发送 Ctrl/Command，而不是仅发送裸 QWERTY 字母。
- home-row hold-tap 的 tap 分支指向对应物理位置的 mod-morph，不能把 Dvorak 字符简单改成字母名却遗漏快捷键分支。
- MODE 切换与 FLASH 请求交给 ZMK worker / 行为接口，LVGL 不直接忙等或在中断中修改键位。
- 版本/构建指纹生成、单目标构建与 UF2 容量门槛保持可复现。

### Module 仓库

- 增加设备页、模式选择页、刷机确认状态机，并接入主屏上滑。
- MAC / WIN 的 modifier 文案与图标改为运行时显示：MAC 显示 CMD/OPT，WIN/GAME 显示 WIN/ALT；必须与真实键位模式同步。
- 状态页显示基础模式和临时层，避免只看到 FN 却不知道当前 OS 模式。
- 三种外观布局仍共享同一模式状态，切换外观不改变键位。
- 新的设备页和对话框共享单实例，保留 partial LVGL buffer 与不阻塞 HID 的执行方式。

### 体积和恢复

当前三布局映像的 UF2 地址结束于 `0xA3700`，距旧 Bootloader 的 `0xAD000` 上限余 39,168 B。新 UI、行为和 keymap 能否一起放入，必须由最终构建与 `verify-dongle-uf2.py` 判断，不能提前保证。RAM 也要重新测量。

进入刷机模式不等于更新 Bootloader。保留当前已验证三布局 UF2、原始 qwerty 配置和 RST–GND 恢复路径。是否需同步刷左右键盘，先核对其 split 角色、位置映射与协议版本；不因为修改 Dongle 键位就默认要求重刷或删除配对。

## 6. 实施和验收顺序

1. **设备页版**：只加上滑、真实设备信息和双重确认的 FLASH，保留当前键位。测试误触取消、NICENANO 挂载、回到应用、原配对保留、亮度页和三布局回归。
2. **输入模式版**：新增用户专用 MAC-DV / WIN-DV / GAME 键位、共用 FN 和模式选择，联动真实状态显示。先测试固定物理修饰键，再接入 home-row hold-tap。
3. **两台主机验收**：逐字母核对 Dvorak，Ctrl/Command-QWERTY 的 C/V/X/Z/A/S/W/T 及标点；左右修饰键、Shift 组合、先松修饰键和先松字母两种顺序均不能卡键。
4. **游戏验收**：WASD 长按、斜向移动、Shift+W、Ctrl+W、Space 连按、媒体/F1–F12、进入/退出 GAME；不把正常组合误识别为层或宏。
5. **唤醒和长期测试**：闲置熄屏后键盘唤醒，第一键不丢；USB 切换器反复切换两台主机；同时滑屏、调光、打字和使用轨迹球时无漏键与卡键。
6. 通过后记录实机结果、固定源码/依赖版本并安排最终 CI。构建通过与物理验收分别记录。

本轮不安排布局记忆、可调休眠时间、环境光传感器、蓝牙主机自动切换或新机械件。

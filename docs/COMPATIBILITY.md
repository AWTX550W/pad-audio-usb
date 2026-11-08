# 不同平板的适配指引

本项目只在 **HUAWEI DBY2-W00 / Android 12** 上做过完整实测。其他设备大概率也能用，但**开发者选项路径、授权方式、音频实现细节**各家不同，照着 README 做可能会卡在某一步。

这份文档解决两件事：

1. **你的平板跟我的不一样，怎么自己调** —— 第 2、3 节；
2. **你不想自己调，想让自己常用的 AI 助手帮你改** —— 直接用第 4 节的提示词。

---

## 1. 先做 30 秒自检

不管什么牌子，先跑这两条命令判断「能不能救」：

```bat
scrcpy\adb.exe devices
scrcpy\adb.exe shell getprop ro.build.version.release
scrcpy\adb.exe shell getprop ro.build.version.sdk
```

判读方式：

| `adb devices` 输出 | 含义 | 下一步 |
|--------------------|------|--------|
| `xxxxxx    device` | 已授权，通了 | 直接双击 bat 试 |
| `xxxxxx    unauthorized` | 连上了但没授权 | 看第 2 节授权部分 |
| `xxxxxx    offline` | 授权状态坏了 | `adb kill-server` 后重新插线 |
| 列表为空 | 根本没识别到设备 | 看第 2 节的线材 / 驱动 / 模式问题 |
| `adb` 报找不到设备 | 同上 | 同上 |

再看 SDK 版本，这决定用哪个音源参数：

| SDK | Android | 可用音源 | 说明 |
|-----|---------|----------|------|
| **≥ 30** | 11+ | `output`（推荐） | 抓全局输出并静音平板，效果最好 |
| 29 | 10 | `playback` 勉强可用 | 应用可以 opt-out，容易被单个 App 规避 |
| ≤ 28 | 9 及以下 | 基本无解 | 系统不提供音频捕获接口，建议改用 3.5mm 音频线 |

---

## 2. 各家平板的具体差异

### 2.1 开发者选项怎么开

都是「连点版本号 7 次」，但入口位置不一样：

| 品牌 | 路径（找不到就在设置里搜「版本号」） |
|------|--------------------------------------|
| 华为 / 荣耀 | 设置 → 关于平板电脑 → 连点「版本号」 |
| 小米 / 红米 / POCO | 设置 → 我的设备 → 全部参数 → 连点「MIUI 版本」或「OS 版本」 |
| OPPO / 一加 / realme | 设置 → 关于本机 → 版本信息 → 连点「版本号」 |
| vivo / iQOO | 设置 → 系统管理 → 关于手机 → 连点「软件版本号」 |
| 三星 | 设置 → 关于手机 → 软件信息 → 连点「内部版本号」 |
| 原生 Android / Pixel | 设置 → 关于手机 → 连点「版本号」 |

### 2.2 授权这一步最容易翻车

**小米 / 红米 / POCO**：开发者选项里除了「USB 调试」，还有一个 **「USB 调试（安全设置）」**，必须一起打开。开这个通常要求**登录小米账号并插卡联网**，且会弹「是否允许通过 USB 调试修改权限或模拟点击」，选允许。只开第一个的话，`adb devices` 可能显示 device 但 shell 命令被拒。

**OPPO / 一加 / realme**：同样有「**USB 调试（安全设置）**」开关，需要单独打开。

**vivo / iQOO**：首次连接会弹「USB 调试授权」，但在部分系统上还要求在「开发者选项 → USB 调试」附近再确认一次「允许 USB 调试」。

**三星**：连接后状态栏下拉，把 USB 用途从「仅充电」改成「**传输文件 / MTP**」，否则 adb 可能连不上。

**所有品牌通用**：如果 `unauthorized` 一直不变，试这个顺序 ——
1. 平板上「撤销 USB 调试授权」；
2. 电脑上 `scrcpy\adb.exe kill-server`；
3. 拔线重插，重新点「允许」，勾选「始终允许」。

### 2.3 鸿蒙（HarmonyOS）要分清版本

- **HarmonyOS 2 / 3 / 4（含 EMUI）**：底层仍是 AOSP 兼容层，**adb 可用**，本项目适用。我实测的 DBY2-W00 就属于这一类（`ro.build.version.release` 报 12）。
- **HarmonyOS NEXT / 鸿蒙 5**：**完全移除了 AOSP，没有 adb**。`adb devices` 永远空列表，本项目**用不了**，也别浪费时间调。替代方案只有 3.5mm 音频线或蓝牙音频转发。

判断方法：`adb shell getprop ro.build.version.release` 能返回数字就是兼容 AOSP；报错或无输出、且设置里找不到「开发者选项」，基本就是 NEXT。

---

## 3. 症状 → 改哪一行

| 症状 | 最可能原因 | 怎么改 |
|------|-----------|--------|
| **平板静音了，但电脑没声音** | 音频抓到了但电脑端播放失败 | bat 里去掉 `--no-playback` 之外的干扰，检查电脑默认播放设备；试加大 `--audio-buffer=100` |
| **电脑有声音但断断续续** | USB 带宽或缓冲不足 | `--audio-buffer=60` 调大到 `150`；换 USB 3.0 接口和好一点的线 |
| **声音有但延迟明显（>200ms）** | 缓冲太大或设备编码器慢 | `--audio-buffer=40`；试 `--audio-codec=aac` 换编码器 |
| **平板不静音，两边同时响** | 系统不支持 output 重定向 | 正常现象，改 `--audio-source=output --audio-dup` 反而更可控 |
| **只有部分 App 有声音** | 该 App 做了音频独占或用了 DRM | 无解，属应用层保护 |
| **`--audio-source=output` 直接报错** | 系统版本低于 Android 11 | 降到 `--audio-source=playback`，接受部分 App 抓不到 |
| **`adb devices` 一直是空** | 线是纯充电线 / 没开 USB 调试 / 驱动缺失 | 换数据线；开开发者选项；Windows 装厂商 USB 驱动或让系统自动装 |
| **能连上，一跑就 `Could not find scrcpy-server`** | 安装不完整 | 删掉 `scrcpy\` 重新跑 `install.bat` |
| **跑起来立刻退出，无提示** | 权限或 server 推送被安全策略拦截 | 用 `scrcpy.exe --no-video --audio-source=output -V debug` 看详细日志 |

### 手动调试的命令模板

bat 被隐藏了细节，排查时直接跑完整命令看得更清楚：

```bat
cd /d "%~dp0"
scrcpy\scrcpy.exe --no-video --audio-source=output --audio-buffer=60 -V debug
```

`-V debug` 会打印编码器选择、音频流建立、解码器初始化全过程。看到 `c2.android.opus.encoder` / Demuxer / Decoder 都正常，说明链路通了；卡在哪一步一目了然。

### 确认「到底有没有真的抓到声音」

这一步很多人跳过，导致误判。用录音 + 电平测量验证：

```bat
scrcpy\scrcpy.exe --no-video --audio-source=output --no-playback --audio-codec=raw -r test.wav
```

录 15 秒后按 `Ctrl+C`，然后：

```bat
ffmpeg -i test.wav -af volumedetect -f null -
```

看 `max_volume`：
- **接近 -91 dB** → 抓到的是一条静音流，通路有问题或平板当时没出声；
- **-20 dB 到 0 dB** → 正常，声音是真的抓到了。

注意 `-r test.wav` **必须配 `--audio-codec=raw`**，否则报 `Recording to WAV file requires a RAW audio stream`。

---

## 4. 让 AI 帮你改（直接复制这段）

不想自己一条条试？把下面整段复制给你的 AI 助手（WorkBuddy / Claude / ChatGPT / Cursor 都行），它会读你的环境、定位问题、改脚本。

> 我在用一个开源小项目 `pad-audio-usb`，作用是把安卓平板的声音通过 USB 线转发到电脑播放。原理是调用 scrcpy 的 `--no-video --audio-source=output`。
>
> 项目已在本机，路径是：`<把实际路径填这里>`。
> 主要文件：`run.bat`（主程序，实际执行 scrcpy）、`install.bat`（下载安装 scrcpy 到 `scrcpy\` 子目录）。
>
> **我的问题**：`<把具体症状写这里，例如「平板静音了但电脑完全没声音」>`
>
> **我的设备信息**（我已跑过，原样贴给你）：
> ```
> <粘贴 adb devices 的输出>
> <粘贴 ro.build.version.release 和 ro.build.version.sdk 的输出>
> 平板品牌型号：<例如 小米平板 6 Pro>
> Windows 版本：<例如 Win11 23H2>
> ```
>
> 请你按这个顺序帮我：
> 1. 先判断是「环境没通」还是「参数不对」——不要一上来就改脚本；
> 2. 用 `scrcpy\adb.exe` 和 `scrcpy\scrcpy.exe` 实际跑命令验证，`-V debug` 拿真实日志，别猜；
> 3. 需要改参数就只改 `run.bat` 里那一行 scrcpy 命令，并说明每个参数为什么这么调；
> 4. 改完必须实测验证：用 `--no-playback --audio-codec=raw -r test.wav` 录一段，再用 `ffmpeg -af volumedetect` 看 `max_volume` 是否明显高于 -91 dB。**只有电平真的上来才算修好，不要只看进程没报错。**
> 5. 如果结论是这台设备物理上做不到（例如鸿蒙 NEXT 没有 adb），直接告诉我不行和原因，不要硬凑方案。
>
> 另外注意两个我知道的坑：`run.bat` 必须是 **CRLF 换行**（LF 会让 cmd 解析中文错位）；bat 里 `echo` 后面的 `->` 会被当成重定向，必须用全角 `→`。

这套提示词的要点是：**给了设备信息、给了验证方法、明确禁止「进程没报错就算成功」**。AI 拿着这个基本能自己走完排查闭环，不用你来回猜。

---

## 5. 已知不适用的场景

| 场景 | 结论 |
|------|------|
| 鸿蒙 NEXT / 鸿蒙 5 平板 | 无 adb，用不了 |
| iPad | 无 adb，用不了（iPad 可走 macOS 的「隔空播放」或音频线） |
| Android 9 及以下 | 系统无音频捕获接口，改用音频线 |
| 平板只支持「仅充电」USB 模式 | 换线或检查接口，无法建立 adb |
| 需要抓 DRM 保护内容 | 抓不到，属版权保护 |

---

## 6. 欢迎反馈机型结果

如果你在别的机型上跑通了（或确认跑不通），欢迎开 issue 说一声，附上：

- 品牌 + 型号
- `ro.build.version.sdk`
- 你改动了哪个参数
- `volumedetect` 的 `max_volume` 数值

这样这份兼容表就能慢慢变准，后面的人少踩坑。

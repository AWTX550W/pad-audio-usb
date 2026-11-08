# Pad Audio USB · 平板声音转电脑

用一根 **USB 线**，把安卓平板的声音接到电脑上播放。

专门解决一个很具体的场景：**平板通过 spacedesk 当电脑的扩展屏，平板自己打开本地应用时，声音还是从平板出来，回不到电脑。**

> EN: Route your Android tablet's local audio to your PC over a plain USB cable — no Wi-Fi, no extra app on the tablet, one double-click.

---

## 它解决什么问题

用 spacedesk 做扩展屏时，音频是**单向**的：

```
电脑的桌面 + 电脑自己的声音  ──→  平板（显示 / 播放）   ✅ spacedesk 能做
平板本地应用的声  ──────────→  电脑                    ❌ 没有任何通道
```

spacedesk 本质是「视频帧 + 电脑音频」的推送器，它没有「平板 → 电脑」的反向音频通道。华为多屏协同也一样做不到把平板本地音频送回电脑。

想反过来，必须另开一条通道。本项目用 **scrcpy 的音频转发**，走 **ADB over USB**：

```
平板本地应用的声音  ──ADB/USB──→  电脑音箱 / 耳机     ✅ 本项目
```

---

## 为什么选这条路

| 方案 | 走什么通道 | 平板要不要装 App | 占不占网络 | 每次使用要配置吗 |
|------|-----------|-----------------|-----------|-----------------|
| **本项目（scrcpy）** | ADB over USB | 不用 | **不占** | **不用，双击即用** |
| Audio Relay / SoundWire | 局域网 | 要装 | 占，和 spacedesk 抢带宽 | 要连一次 |
| 蓝牙音频转发 | 蓝牙 | 不用 | 不占 | 要配对，延迟 150–300ms |
| 3.5mm 音频对录线 | 模拟线 | 不用 | 不占 | 插线即可，但要额外的线 |

关键优势：**走的是 USB 数据通道，不是网络**。所以平板照常上网、spacedesk 画面完全不受影响、延迟比无线方案低。

---

## 前置要求

| 项 | 要求 |
|----|------|
| 系统 | Windows 10 1803 及以上（需要自带的 `curl` 和 `tar`） |
| 平板 | **Android 11 及以上**（`--audio-source=output` 的硬性要求） |
| 线材 | USB **数据线**（纯充电线不行） |
| 平板设置 | 开发者选项 → **USB 调试** 打开，并在弹窗里点「允许」 |

> 华为 / 荣耀设备：`设置 → 关于平板 → 连点版本号 7 次` 开启开发者选项，再进 `设置 → 系统和更新 → 开发人员选项 → USB 调试`。

---

## 使用

1. **首次安装**：双击 `install.bat`，自动下载 scrcpy 到本目录的 `scrcpy\` 文件夹（优先走镜像加速，失败自动回退 GitHub 官方源）。
2. **连接平板**：USB 线插好，平板弹出「允许 USB 调试吗？」时点**允许**，建议勾选「始终允许此计算机」。
3. **开始转发**：双击 `平板声音到电脑.bat`。看到「平板已连接 / 运行中」就成了。
4. **停止**：关掉那个黑窗口，或按 `Ctrl+C`。平板会自动恢复外放。

脚本会自动检查连接状态，没插好 / 没授权 / 没装 scrcpy 都会给出具体提示，不会一闪而过。

---

## 运行时会发生什么

- 平板的**全部音频输出**被转发到电脑，由电脑当前的默认音频设备播放
- **平板自身会被静音**（这是 `--audio-source=output` 的设计行为：音频被重定向，不再走平板扬声器）
- 电脑自己的声音照常播放，两边的声音混在一起输出
- **不弹任何视频窗口**（`--no-video`），所以 spacedesk 的扩展屏画面完全不受干扰

想让平板和电脑**同时出声**？把 bat 里的 `--audio-source=output` 改成 `--audio-source=playback --audio-dup`。代价是部分应用会拒绝被捕获（见下）。

---

## 已知限制

| 限制 | 说明 |
|------|------|
| **DRM 内容抓不到** | 部分流媒体（如 Netflix 等受版权保护的内容）会静音。普通视频、音乐、游戏、B 站、抖音正常 |
| **要求 Android 11+** | `output` 音源需要 Android 11（API 30）以上；更低版本只能试 `--audio-source=playback`，且应用可主动 opt-out |
| **锁屏 / 拔线会断** | 转发中断后重新双击 bat 即可 |
| **平板会静音** | 见上一节，这是预期行为；不想静音就换 `playback + --audio-dup` |
| **首次要授权** | USB 调试授权是一次性的；但某些系统在 USB 调试长时间关闭后会要求重新授权 |

---

## 项目结构

```
pad-audio-usb/
├── install.bat              # 首次安装：下载 scrcpy 到 scrcpy\
├── 平板声音到电脑.bat        # 主程序：双击开始转发
├── run.bat                  # 同上（英文名别名，内容一致）
├── docs/
│   └── VERIFICATION.md      # 实测验证记录（含客观测量数据）
├── LICENSE
└── .gitignore
```

`scrcpy\` 目录由 `install.bat` 生成，不进版本库。

---

## 技术细节

实际执行的命令就是一条：

```bat
scrcpy.exe --no-video --audio-source=output --audio-buffer=60
```

| 参数 | 作用 |
|------|------|
| `--no-video` | 不传视频、不开窗口，所以不影响 spacedesk 的扩展屏 |
| `--audio-source=output` | 捕获设备**全部**音频输出，并**自动禁用设备端播放** |
| `--audio-buffer=60` | 60ms 缓冲，兼顾延迟与抗抖动 |

底层是 scrcpy 把 `scrcpy-server` 推送到平板，以 shell 权限用 `AudioRecord` 的远端混音（REMOTE_SUBMIX）抓取全局输出，Opus 编码后经 ADB 回传，电脑端解码后用 SDL 播放到默认音频设备。

依赖：[scrcpy](https://github.com/Genymobile/scrcpy)（Apache-2.0）。

---

## 验证

不是「理论上可以」——有实测数据，见 [`docs/VERIFICATION.md`](docs/VERIFICATION.md)。

简要结论：推送 440Hz 测试音到平板播放，scrcpy 录制回来的音频里，该时段主频精确为 **440.0 Hz**、电平恒定，峰值 **-0.4 dB**，证明音频通路完整无损。

---

## 许可

[MIT](LICENSE) © 2026 AWTX550W

本项目只是对 scrcpy 的一次场景化封装，真正的功劳属于 scrcpy 的作者。

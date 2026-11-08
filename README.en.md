# Pad Audio USB

Route your Android tablet's audio to your PC over a **single USB cable**.

Built for one specific, surprisingly common situation: **you use your tablet as a second monitor via spacedesk, the desktop's sound already comes out of your PC — but as soon as you open a local app on the tablet, its audio plays from the tablet's own speakers and there is no way to get it back to the PC.**

> 中文说明见 [README.md](README.md)

---

## The problem

spacedesk pushes video frames plus the PC's own audio **one way**:

```
PC desktop + PC audio  ──→  tablet (display / playback)   ✅ spacedesk does this
tablet's local audio   ──→  PC                            ❌ no such channel exists
```

spacedesk is a frame pusher, not a two-way audio bridge. Huawei Multi-Screen Collaboration doesn't solve it either — it also has no path for pushing the tablet's local audio back to the PC.

You need a separate channel. This project uses **scrcpy's audio forwarding** over **ADB over USB**:

```
tablet's local audio  ──ADB/USB──→  PC speakers / headphones    ✅ this project
```

---

## Why this route

| Approach | Channel | App on tablet | Network impact | Setup each time |
|----------|---------|---------------|----------------|-----------------|
| **This project (scrcpy)** | ADB over USB | Not needed | **None** | **None — double-click** |
| Audio Relay / SoundWire | LAN | Required | Competes with spacedesk | Reconnect every time |
| Bluetooth audio sink | Bluetooth | Not needed | None | Pairing, 150–300 ms latency |
| 3.5 mm audio cable | Analog | Not needed | None | Plug in, but you need the cable |

The key point: **it uses the USB data channel, not the network.** Your tablet keeps its internet connection, spacedesk's picture is untouched, and latency is lower than any wireless option.

---

## Requirements

| Item | Requirement |
|------|-------------|
| OS | Windows 10 1803+ (needs the built-in `curl` and `tar`) |
| Tablet | **Android 11+** — hard requirement for `--audio-source=output` |
| Cable | A USB **data** cable (charge-only cables won't work) |
| Tablet settings | Developer options → **USB debugging** on, and tap **Allow** when prompted |

> Huawei / Honor: `Settings → About tablet → tap Build number 7 times`, then `Settings → System & updates → Developer options → USB debugging`.
>
> On Xiaomi / OPPO / vivo you may also need the separate **"USB debugging (Security settings)"** toggle. See [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md) for per-vendor details.

---

## Usage

1. **Install once**: double-click `install.bat`. It downloads scrcpy into `scrcpy\` in this folder (mirror first for speed, automatic fallback to the official GitHub release).
2. **Plug in the tablet**: when it asks "Allow USB debugging?", tap **Allow** and check "Always allow from this computer".
3. **Start forwarding**: double-click `run.bat`. When you see the connected / running message, it's working.
4. **Stop**: close the console window or press `Ctrl+C`. The tablet restores its own speaker output immediately.

The script checks the connection state first and gives a specific message for each failure (cable, permission, missing scrcpy) instead of flashing and vanishing.

---

## What happens while it runs

- The tablet's **entire audio output** is forwarded to the PC and played on the PC's current default output device
- **The tablet itself is muted** — this is by design in `--audio-source=output`: the audio is redirected to the remote submix, so it no longer reaches the tablet speakers
- The PC's own audio keeps playing; both are mixed together
- **No video window is opened** (`--no-video`), so your spacedesk extended screen is completely unaffected

Want sound from both devices at once? Change `--audio-source=output` to `--audio-source=playback --audio-dup` in the script. The trade-off is that some apps opt out of being captured.

---

## Known limitations

| Limitation | Details |
|------------|---------|
| **DRM content can't be captured** | Some streaming services (Netflix and similar protected content) will be silent. Regular video, music, games, YouTube, TikTok are fine |
| **Android 11+ required** | The `output` source needs API 30+. On older versions only `--audio-source=playback` is available, and apps can opt out |
| **Breaks on lock screen / cable pull** | Just double-click the script again |
| **Tablet gets muted** | Expected behaviour, see above |
| **First-time authorization** | One-off, but some ROMs ask again after USB debugging has been off for a while |
| **HarmonyOS NEXT is not supported** | It dropped AOSP entirely, so there is no adb. HarmonyOS 2/3/4 still work |

---

## Project layout

```
pad-audio-usb/
├── install.bat              # one-time: download scrcpy into scrcpy\
├── run.bat                  # main launcher
├── 平板声音到电脑.bat        # same script, Chinese filename alias
├── docs/
│   ├── VERIFICATION.md      # measured end-to-end evidence
│   └── COMPATIBILITY.md     # per-vendor setup, troubleshooting, AI prompt template
├── scripts/
│   └── check_repo.py        # static checks (bat line endings, redirection traps, links)
└── .github/workflows/check.yml
```

`scrcpy\` is generated by `install.bat` and is not tracked.

---

## How it works

The whole thing is one command:

```bat
scrcpy.exe --no-video --audio-source=output --audio-buffer=60
```

| Flag | Purpose |
|------|---------|
| `--no-video` | No video stream, no window — spacedesk keeps the extended screen |
| `--audio-source=output` | Capture the device's full audio output **and disable playback on the device** |
| `--audio-buffer=60` | 60 ms buffer — a balance between latency and jitter resistance |

Under the hood, scrcpy pushes `scrcpy-server` to the tablet, captures global output through `AudioRecord` on the `REMOTE_SUBMIX` device with shell privileges, encodes to Opus, streams it back over ADB, and decodes it on the PC with SDL to the default audio device.

Depends on [scrcpy](https://github.com/Genymobile/scrcpy) (Apache-2.0).

---

## Verification

Not a "should work in theory" claim — there are measurements in [docs/VERIFICATION.md](docs/VERIFICATION.md).

Short version: a 440 Hz test tone was pushed to the tablet and played, then the captured stream was recorded and analysed. The tone segment measured **exactly 440.0 Hz** at a constant level, with an overall peak of **-0.4 dB** — the audio path is complete and lossless.

The control run (tablet silent) measured **-91 dB**, i.e. digital silence. That contrast is the actual proof: "the process started without errors" and "real audio came through" are different things.

---

## Using a different tablet?

Only HUAWEI DBY2-W00 / Android 12 has been fully verified. Other devices will most likely work, but developer-option paths, authorization quirks and audio implementations vary by vendor.

[docs/COMPATIBILITY.md](docs/COMPATIBILITY.md) covers:

- a 30-second self-check,
- per-vendor paths and the authorization traps (Xiaomi, OPPO, vivo, Samsung…),
- a symptom → fix table,
- **a ready-to-paste prompt so your own AI assistant can adapt the scripts for your device.**

---

## License

[MIT](LICENSE) © 2026 AWTX550W

This project is just a scenario-specific wrapper around scrcpy. The real credit belongs to scrcpy's author.

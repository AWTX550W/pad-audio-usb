#!/usr/bin/env python3
"""仓库静态检查。

针对本项目反复踩过的两个真实坑做强制校验：
  1. .bat 必须是 CRLF 换行 —— LF 会让 cmd 解析多字节中文时行错位；
  2. .bat 里 echo / title 的自然语言箭头 `->` 要写成全角 `→`，
     否则 cmd 把它当重定向符号，命令会变成往文件写。

另外检查文件编码、README 相对链接、以及是否有本机绝对路径泄漏。

无第三方依赖，Windows / Linux / macOS 均可运行。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Windows 控制台 / CI runner 的默认 stdout 编码可能是 cp1252 或 cp936，
# 直接 print 中文会抛 UnicodeEncodeError。强制切到 UTF-8。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

errors: list[str] = []
warnings: list[str] = []


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


# 版本库外的目录：安装产物、依赖、git 元数据
EXCLUDE_DIRS = {".git", "scrcpy", "node_modules", "__pycache__", ".venv"}


def _ignored(p: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in p.relative_to(ROOT).parts)


def iter_bat() -> list[Path]:
    return sorted(p for p in ROOT.rglob("*.bat") if not _ignored(p))


def iter_markdown() -> list[Path]:
    return sorted(p for p in ROOT.rglob("*.md") if not _ignored(p))


# ---------------------------------------------------------------- BAT 检查

def check_bat(path: Path) -> None:
    raw = path.read_bytes()
    name = rel(path)

    # 1. BOM
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append(f"{name}: 含 UTF-8 BOM，cmd 会把 BOM 当命令内容，删掉 BOM")

    # 2. 裸 LF（CRLF 检查）
    bare_lf = raw.count(b"\n") - raw.count(b"\r\n")
    if bare_lf > 0:
        total = raw.count(b"\n")
        errors.append(
            f"{name}: 有 {bare_lf}/{total} 行是 LF 换行，必须是 CRLF。"
            f"用 '(Get-Content -Raw x) -replace \"\\n\",\"`r`n\"' 重写，"
            f"并确认 .gitattributes 里有 '*.bat text eol=crlf'"
        )

    # 3. UTF-8 可解码
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"{name}: 不是合法 UTF-8（{exc}），统一用 UTF-8 无 BOM")
        return

    lines = text.splitlines()

    # 4. 重定向陷阱
    for idx, line in enumerate(lines, start=1):
        s = line.strip()
        low = s.lower()

        # title 行里的任何 > 都是错的
        if low.startswith("title") and ">" in s:
            errors.append(
                f"{name}:{idx}: title 行含 '>'，cmd 会当成重定向 → {s[:60]!r}。改用全角 '→'"
            )

        # echo 行里的自然语言箭头
        if low.startswith("echo"):
            body = s[4:].lstrip(".")
            # 排除合法重定向：>nul / > file / 2>&1 / >>append
            illegal = re.search(r"(?<![0-9])->|\s>\s(?![a-zA-Z0-9_.\\/:])", body)
            if "->" in body:
                errors.append(
                    f"{name}:{idx}: echo 行含 '->'，会被当成重定向 → {s[:60]!r}。改用全角 '→'"
                )
            elif illegal and re.search(r"\s>\s(?![a-zA-Z0-9_.\\/:])", body):
                errors.append(
                    f"{name}:{idx}: echo 行含孤立 '>' → {s[:60]!r}。改用全角 '→'"
                )

    # 5. 以 @echo off 开头（软提示）
    first = next((ln.strip().lower() for ln in lines if ln.strip()), "")
    if first != "@echo off":
        warnings.append(f"{name}: 首行不是 '@echo off'（当前 {first!r}），确认是否有意为之")

    # 6. 中文输出依赖代码页
    has_cjk = any("\u4e00" <= ch <= "\u9fff" for ch in text)
    chcp = any(ln.strip().lower().startswith("chcp") for ln in lines)
    if has_cjk and not chcp:
        warnings.append(
            f"{name}: 含中文但没设 chcp，若控制台非 UTF-8 代码页可能显示乱码"
        )


# ----------------------------------------------------------- Markdown 检查

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def check_md(path: Path) -> None:
    name = rel(path)
    text = path.read_text(encoding="utf-8")

    for target in LINK_RE.findall(text):
        t = target.strip().split(" ")[0].strip("<>")
        if not t or t.startswith(("http://", "https://", "mailto:", "#")):
            continue
        # 去掉锚点
        anchor_free = t.split("#")[0]
        if not anchor_free:
            continue
        target_path = (path.parent / anchor_free).resolve()
        if not target_path.exists():
            errors.append(f"{name}: 相对链接指向不存在的文件 → {t}")


# --------------------------------------------------------- 本机路径泄漏检查

LEAK_PATTERNS = [
    (re.compile(r"[A-Za-z]:\\\\Users\\\\[A-Za-z0-9_.-]+"), "Windows 用户目录绝对路径"),
    (re.compile(r"[A-Za-z]:\\Users\\[A-Za-z0-9_.-]+"), "Windows 用户目录绝对路径"),
    (re.compile(r"/Users/[A-Za-z0-9_.-]+/"), "macOS 用户目录绝对路径"),
    (re.compile(r"[A-Za-z]:\\\\WorkBuddy\\\\|/WorkBuddy/"), "个人工作目录路径"),
]

LEAK_ALLOW = {"docs/COMPATIBILITY.md"}  # 提示词模板里的占位说明允许出现示例


def check_leak(path: Path) -> None:
    name = rel(path)
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return
    for pat, label in LEAK_PATTERNS:
        for m in pat.finditer(text):
            snippet = m.group(0)
            if name in LEAK_ALLOW:
                continue
            warnings.append(f"{name}: 疑似{label} → {snippet}（开源仓库建议脱敏）")


# ------------------------------------------------------------------- main

def main() -> int:
    bats = iter_bat()
    mds = iter_markdown()

    print(f"仓库根目录: {ROOT}")
    print(f"检查 .bat: {len(bats)} 个")
    for p in bats:
        print(f"  - {rel(p)}")
    print(f"检查 .md : {len(mds)} 个\n")

    for p in bats:
        check_bat(p)
    for p in mds:
        check_md(p)

    for p in list(bats) + list(mds):
        check_leak(p)

    if warnings:
        print(f"[WARN] {len(warnings)} 条提示：")
        for w in warnings:
            print(f"  ! {w}")
        print()

    if errors:
        print(f"[FAIL] {len(errors)} 个错误：")
        for e in errors:
            print(f"  x {e}")
        print("\n检查未通过。")
        return 1

    print("[OK] 全部检查通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

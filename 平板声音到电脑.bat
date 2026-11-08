@echo off
chcp 65001 >nul
setlocal
title 平板声音转发到电脑

set "ROOT=%~dp0"
set "ADB=%ROOT%scrcpy\adb.exe"
set "SCRCPY=%ROOT%scrcpy\scrcpy.exe"

echo ================================================
echo    平板声音   →   电脑音箱 / 耳机
echo ================================================
echo.

if not exist "%SCRCPY%" (
    echo [错误] 还没安装 scrcpy
    echo        请先双击本目录下的 install.bat 完成安装
    echo.
    pause
    exit /b 1
)

echo [1/3] 正在检查平板连接 ...
"%ADB%" start-server >nul 2>&1
set "STATE="
for /f "delims=" %%s in ('%ADB% get-state 2^>nul') do set "STATE=%%s"

if /i not "%STATE%"=="device" (
    echo.
    echo  [!] 没检测到已授权的平板（当前状态：%STATE%）
    echo      请检查：
    echo        1. USB 线已插好（数据线，不是纯充电线）
    echo        2. 平板已开启 开发者选项 - USB 调试
    echo        3. 平板上弹出「允许 USB 调试」时，点允许并勾选始终允许
    echo.
    pause
    exit /b 1
)

echo       平板已连接
echo.
echo [2/3] 启动音频转发 ...
echo.
echo   运行期间：
echo     - 平板所有声音改由电脑播放（平板自身静音）
echo     - 不占用网络，不影响 spacedesk 扩展屏画面
echo     - 电脑自己的声音照常播放，两者混在一起
echo.
echo [3/3] 运行中：关闭本窗口 或 按 Ctrl+C 停止并恢复平板外放
echo.
echo ------------------------------------------------
echo.

pushd "%ROOT%scrcpy"
"%SCRCPY%" --no-video --audio-source=output --audio-buffer=60
popd

echo.
echo ------------------------------------------------
echo.
echo 已停止，平板恢复原音量输出。
pause

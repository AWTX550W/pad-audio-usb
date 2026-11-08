@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ================================================
echo    Pad Audio USB  -  安装 scrcpy 运行环境
echo ================================================
echo.

if exist "scrcpy\scrcpy.exe" (
    echo [跳过] scrcpy 已安装：%~dp0scrcpy
    goto :done
)

where curl >nul 2>&1
if errorlevel 1 (
    echo [错误] 系统缺少 curl 命令。
    echo        请升级到 Windows 10 1803 及以上，或手动下载 scrcpy 后解压到 scrcpy\ 目录
    echo        https://github.com/Genymobile/scrcpy/releases
    echo.
    pause
    exit /b 1
)

set "VER=5.0.1"
set "PKG=scrcpy-win64-v%VER%"
set "GH=https://github.com/Genymobile/scrcpy/releases/download/v%VER%/%PKG%.zip"

echo [1/3] 正在下载 scrcpy %VER% ...
curl -L --max-time 300 -o "%PKG%.zip" "%GH%"
if not exist "%PKG%.zip" (
    echo.
    echo [提示] 官方源不可达，改用镜像重试 ...
    curl -L --max-time 300 -o "%PKG%.zip" "https://cors.isteed.cc/%GH%"
)
if not exist "%PKG%.zip" (
    echo.
    echo [错误] 下载失败。请手动下载：
    echo        %GH%
    echo        解压后把里面的文件放进本目录的 scrcpy\ 文件夹
    echo.
    pause
    exit /b 1
)

echo [2/3] 正在解压 ...
tar -xf "%PKG%.zip"
if not exist "%PKG%\scrcpy.exe" (
    echo [错误] 解压结果异常，未找到 %PKG%\scrcpy.exe
    echo        请手动解压后把内容放入 scrcpy\ 文件夹
    echo.
    pause
    exit /b 1
)

echo [3/3] 正在归位 ...
if not exist "scrcpy" mkdir "scrcpy"
xcopy /e /i /y /q "%PKG%\*" "scrcpy\" >nul
rmdir /s /q "%PKG%"
del /q "%PKG%.zip"

:done
echo.
echo --------------------------------------------------
echo 安装完成。双击「平板声音到电脑.bat」开始使用。
echo --------------------------------------------------
echo.
pause

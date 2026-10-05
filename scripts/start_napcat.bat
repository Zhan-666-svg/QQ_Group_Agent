@echo off
chcp 65001 >nul
title NapCatQQ 协议端网关

cd /d "D:\QQ_Group_Agent\napcat"

set "QQPath=D:\Program Files\Tencent\QQNT\QQ.exe"

if not exist "%QQPath%" set "QQPath=C:\Program Files\Tencent\QQNT\QQ.exe"
if not exist "%QQPath%" set "QQPath=C:\Program Files (x86)\Tencent\QQNT\QQ.exe"

if not exist "%QQPath%" (
    echo [错误] 未能找到 QQ.exe，请检查 QQ 是否已安装在 D:\Program Files\Tencent\QQNT\
    pause
    exit /b 1
)

echo ========================================================
echo   NapCatQQ 协议端网关启动中...
echo   QQNT 目标路径: %QQPath%
echo ========================================================

%SystemRoot%\System32\tasklist.exe /fi "imagename eq QQ.exe" 2>nul | %SystemRoot%\System32\find.exe /i "QQ.exe" >nul
if %ERRORLEVEL% == 0 (
    echo [提示] 检测到当前电脑已有 QQ 进程正在运行。
    echo 如启动后无法弹出二维码或直接退出，请先退出右下角托盘 QQ，再重新运行此脚本。
    echo.
)

set NAPCAT_PATCH_PACKAGE=%cd%\qqnt.json
set NAPCAT_LOAD_PATH=%cd%\loadNapCat.js
set NAPCAT_INJECT_PATH=%cd%\NapCatWinBootHook.dll
set NAPCAT_LAUNCHER_PATH=%cd%\NapCatWinBootMain.exe
set NAPCAT_MAIN_PATH=%cd%\napcat.mjs

set NAPCAT_MAIN_PATH=%NAPCAT_MAIN_PATH:\=/%
echo (async () =^> {await import("file:///%NAPCAT_MAIN_PATH%")})() > "%NAPCAT_LOAD_PATH%"

"%NAPCAT_LAUNCHER_PATH%" "%QQPath%" "%NAPCAT_INJECT_PATH%" %*

pause

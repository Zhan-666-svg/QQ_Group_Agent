@echo off
chcp 65001 >nul
set NAPCAT_PATCH_PACKAGE=%cd%\qqnt.json
set NAPCAT_LOAD_PATH=%cd%\loadNapCat.js
set NAPCAT_INJECT_PATH=%cd%\NapCatWinBootHook.dll
set NAPCAT_LAUNCHER_PATH=%cd%\NapCatWinBootMain.exe
set NAPCAT_MAIN_PATH=%cd%\napcat.mjs
REM 探测 QQ.exe 路径
set "QQPath="

if exist "D:\Program Files\Tencent\QQNT\QQ.exe" (
    set "QQPath=D:\Program Files\Tencent\QQNT\QQ.exe"
    goto :napcat_boot
)

if exist "C:\Program Files\Tencent\QQNT\QQ.exe" (
    set "QQPath=C:\Program Files\Tencent\QQNT\QQ.exe"
    goto :napcat_boot
)

if exist "C:\Program Files (x86)\Tencent\QQNT\QQ.exe" (
    set "QQPath=C:\Program Files (x86)\Tencent\QQNT\QQ.exe"
    goto :napcat_boot
)

for /f "tokens=2*" %%a in ('reg query "HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\QQ" /v "UninstallString" 2^>nul') do (
    set "RetString=%%~b"
)
if defined RetString (
    for %%a in ("%RetString%") do set "QQPath=%%~dpaQQ.exe"
    if exist "%QQPath%" goto :napcat_boot
)

for /f "tokens=2*" %%a in ('reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\QQ" /v "UninstallString" 2^>nul') do (
    set "RetString=%%~b"
)
if defined RetString (
    for %%a in ("%RetString%") do set "QQPath=%%~dpaQQ.exe"
    if exist "%QQPath%" goto :napcat_boot
)

:napcat_boot
if not exist "%QQpath%" (
    echo [错误] 未能找到有效的 QQ.exe 路径。
    pause
    exit /b
)
echo [信息] 找到 QQ.exe: %QQPath%
set NAPCAT_MAIN_PATH=%NAPCAT_MAIN_PATH:\=/%
echo (async () =^> {await import("file:///%NAPCAT_MAIN_PATH%")})() > "%NAPCAT_LOAD_PATH%"

"%NAPCAT_LAUNCHER_PATH%" "%QQPath%" "%NAPCAT_INJECT_PATH%" %*

REM Optional: -q <QQ_NUMBER> for quick login, omit for QR code login
REM Example: "%NAPCAT_LAUNCHER_PATH%" "%QQPath%" "%NAPCAT_INJECT_PATH%" -q 123456

pause

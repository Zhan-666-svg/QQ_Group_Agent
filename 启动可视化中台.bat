@echo off
chcp 65001 >nul
title QQ群情报抓取与AI研判智能体中台

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 虚拟环境未找到，请确认 D:\QQ_Group_Agent\.venv 是否正常。
    pause
    exit /b 1
)

:: 使用 python.exe 启动，一旦有意外异常窗口不会秒退，并输出错误日志
.venv\Scripts\python.exe gui\app.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo ========================================================
    echo   程序异常退出，退出码: %ERRORLEVEL%
    echo ========================================================
    pause
)

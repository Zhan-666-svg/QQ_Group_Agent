@echo off
chcp 65001 >nul
title QQ群消息抓取智能体监听服务

cd /d "D:\QQ_Group_Agent"

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 虚拟环境未找到，请确认 D:\QQ_Group_Agent\.venv 是否存在。
    pause
    exit /b 1
)

echo ========================================================
echo   启动 QQ 群消息智能体抓取服务...
echo ========================================================

.venv\Scripts\python.exe src\main.py

pause

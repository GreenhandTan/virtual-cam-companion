@echo off
chcp 65001 >nul 2>&1
title VirtualCam Companion
cd /d "%~dp0"
python app.py
if %errorlevel% neq 0 (
    echo.
    echo [!] 启动失败，请确认已运行 install.bat 完成安装
    pause
)

@echo off
chcp 65001 >nul
title BookGuard 珍贵图书数字化保护系统
echo ========================================
echo   BookGuard 珍贵图书数字化保护系统
echo   一键启动脚本
echo ========================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/3] 创建虚拟环境...
cd /d %~dp0backend
if not exist venv (
    python -m venv venv
    echo 虚拟环境创建完成
) else (
    echo 虚拟环境已存在，跳过
)

echo [2/3] 安装依赖...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q
echo 依赖安装完成

echo [3/3] 启动系统...
echo.
echo ========================================
echo   系统启动中...
echo   访问地址: http://localhost:8000
echo   API文档:  http://localhost:8000/docs
echo.
echo   请确保 UmiOCR 已启动并开启 HTTP 服务
echo   UmiOCR 默认地址: http://127.0.0.1:1224
echo.
echo   按 Ctrl+C 停止服务
echo ========================================
echo.
python -m app.main

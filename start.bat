@echo off
chcp 65001 >nul
echo ========================================
echo   BookGuard 珍贵图书数字化保护系统
echo   启动中...
echo ========================================
echo.

echo [1/3] 启动后端服务...
start "BookGuard-Backend" cmd /k "cd /d %~dp0backend && pip install -r requirements.txt -q && python -m app.main"
timeout /t 5 /nobreak >nul

echo [2/3] 安装前端依赖...
cd /d %~dp0frontend
if not exist node_modules (
    echo 首次运行，安装前端依赖...
    call npm install
)

echo [3/3] 启动前端服务...
start "BookGuard-Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   系统已启动！
echo   前端地址: http://localhost:3000
echo   后端地址: http://localhost:8000
echo   API文档:  http://localhost:8000/docs
echo.
echo   请确保 UmiOCR 已启动并开启 HTTP 服务
echo   UmiOCR 默认地址: http://127.0.0.1:1224
echo ========================================
echo.
pause

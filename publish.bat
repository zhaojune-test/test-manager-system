@echo off
chcp 65001 >nul
title 测试管理系统 - 云端发布

echo.
echo ========================================
echo      测试管理系统 - 一键发布
echo ========================================
echo.

REM 检查并启动本地服务
echo [1/4] 启动本地服务...
netstat -ano | findstr :5000 | findstr LISTENING >nul
if %errorlevel%==0 (
    echo        [OK] 服务已在运行
) else (
    start "" python backend/server.py
    timeout /t 3 >nul
    echo        [OK] 服务已启动
)

REM 下载 cloudflared（无需注册）
echo [2/4] 检查穿透工具...
where cloudflared >nul 2>&1
if %errorlevel% neq 0 (
    echo        正在下载 cloudflared...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe'" 2>nul
    move /y cloudflared.exe "C:\Program Files\cloudflared.exe" >nul 2>&1
    set PATH=%PATH%;C:\Program Files
    echo        [OK] 下载完成
) else (
    echo        [OK] cloudflared 已安装
)

REM 启动穿透
echo [3/4] 启动内网穿透...
echo.

start "" cloudflared tunnel --url http://localhost:5000

REM 等待获取链接
timeout /t 8 >nul

REM 提取链接
echo [4/4] 获取访问链接...
echo.

REM 查找 cloudflared 窗口输出中的链接
for /f "tokens=*" %%i in ('powershell -Command "Get-Process cloudflared -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -ne ''} | ForEach-Object {$_.MainWindowTitle}" 2^nul') do (
    echo %%i | findstr "trycloudflare" >nul
    if not errorlevel 1 (
        echo.
        echo ========================================
        echo [OK] 发布成功！
        echo.
        echo 访问链接: %%i
        echo.
        echo 此链接有效期2小时，可分享给任何人
        echo 关闭此窗口后链接失效
        echo ========================================
        pause
        exit
    )
)

echo.
echo [!] 未能自动获取链接
echo     请查看 cloudflared 窗口中的 trycloudflare.com 链接
echo.
pause

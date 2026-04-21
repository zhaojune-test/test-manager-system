@echo off
chcp 65001 >nul
title 测试管理系统 - 长期稳定发布

echo.
echo ========================================
echo    测试管理系统 - Cloudflare Tunnel 部署
echo ========================================
echo.

REM === 配置区域（需要填写）===
set TUNNEL_NAME=oms-test
REM 如果有自定义域名，取消下面注释并填写
REM set CUSTOM_DOMAIN=your-domain.com

REM ============================

REM 检查 cloudflared
echo [1/5] 检查 Cloudflare Tunnel...
where cloudflared >nul 2>&1
if %errorlevel% neq 0 (
    echo        正在下载 cloudflared...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile '%TEMP%\cloudflared.exe'"
    move /y "%TEMP%\cloudflared.exe" "C:\Program Files\cloudflared.exe" >nul
    set "PATH=%PATH%;C:\Program Files"
)

REM 启动本地服务
echo [2/5] 启动本地服务...
netstat -ano | findstr :5000 | findstr LISTENING >nul
if %errorlevel% neq 0 (
    start "" python backend/server.py
    timeout /t 3 >nul
)
echo        [OK] 服务已就绪

REM 启动 tunnel
echo [3/5] 启动 Cloudflare Tunnel...
echo.

REM 检查是否有持久化的 tunnel token
if defined CLOUDFLARE_TUNNEL_TOKEN (
    echo        使用持久化 Token...
    start "" cloudflared service install %CLOUDFLARE_TUNNEL_TOKEN%
) else (
    REM 启动临时 tunnel（链接有效期2小时，但服务长期运行）
    start "" cloudflared tunnel --url http://localhost:5000 --no-autoupdate
)

timeout /t 8 >nul

REM 获取链接
echo [4/5] 获取访问地址...
echo.

for /f "tokens=*" %%i in ('powershell -Command "Get-Process cloudflared -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -ne ''} | ForEach-Object {$_.MainWindowTitle}" 2^nul') do (
    echo %%i | findstr "trycloudflare" >nul
    if not errorlevel 1 (
        echo ========================================
        echo [OK] 部署成功！
        echo.
        echo 访问链接: %%i
        echo.
        echo 提示: 关闭此窗口后链接失效
        echo 要保持长期在线，请:
        echo   1. 注册 Cloudflare 账号
        echo   2. 创建免费的 Tunnel，获取 Token
        echo   3. 设置环境变量 CLOUDFLARE_TUNNEL_TOKEN
        echo ========================================
        pause
        exit
    )
)

echo [!] 请查看 cloudflared 窗口中的链接
echo.
echo [5/5] 提示...
echo.
echo 要获得长期稳定的链接，请:
echo.
echo 步骤1: 注册 Cloudflare (免费)
echo   https://dash.cloudflare.com/sign-up
echo.
echo 步骤2: 创建 Tunnel
echo   在 Zero Trust > Networks > Tunnels > Create Tunnel
echo   选择 "Cloudflared" 类型
echo   获取 Tunnel Token
echo.
echo 步骤3: 配置环境变量（永久生效）
echo   setx CLOUDFLARE_TUNNEL_TOKEN "你的Token"
echo.
echo 步骤4: 重新运行此脚本
echo.
pause

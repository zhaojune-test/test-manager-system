@echo off
title Test Manager - Deploy to GitHub

echo.
echo ========================================
echo    Test Manager - GitHub Deploy Tool
echo ========================================
echo.

REM Check git
echo [1/7] Checking Git...
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Git not found
    echo   Download: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo        [OK] Git found

REM Install GitHub CLI
echo [2/7] Installing GitHub CLI...
where gh >nul 2>&1
if %errorlevel% neq 0 (
    echo        Downloading GitHub CLI...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/cli/cli/releases/latest/download/gh_windows_amd64.msi' -OutFile 'C:\gh.msi'"
    echo        Installing...
    msiexec /i "C:\gh.msi" /quiet /qn
    timeout /t 10 >nul
    del /f "C:\gh.msi" 2>nul
)
echo        [OK] GitHub CLI ready

REM Init repo
echo [3/7] Initializing Git repo...
git init
git add .
git commit -m "Initial commit - Test Manager System"
echo        [OK] Repo initialized

REM GitHub login
echo [4/7] GitHub Login...
echo.
echo        Complete GitHub authorization in the browser
echo.
gh auth login --hostname github.com --web
if %errorlevel% neq 0 (
    echo.
    echo [X] GitHub login failed
    pause
    exit /b 1
)
echo        [OK] GitHub login success

REM Create remote repo
echo [5/7] Creating GitHub repo...
set REPO_NAME=test-manager-system
gh repo create %REPO_NAME% --private --source=. --force
echo        [OK] Repo created

REM Push
echo [6/7] Pushing to GitHub...
git push -u origin main
echo        [OK] Code pushed

echo.
echo ========================================
echo [OK] Done! Code pushed to GitHub!
echo.
echo Next: Deploy to Railway
echo.
echo 1. Open: https://railway.app
echo 2. Login with GitHub
echo 3. Click New Project > Deploy from GitHub
echo 4. Select %REPO_NAME% repo
echo 5. Wait for deployment (~2-3 mins)
echo.
echo You will get a permanent URL to share!
echo ========================================
pause

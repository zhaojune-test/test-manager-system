@echo off
title Test Manager - Step 1: Upload to GitHub

echo.
echo ========================================
echo    Step 1: Upload to GitHub (Manual)
echo ========================================
echo.

echo This script will:
echo   1. Open GitHub in browser to create repo
echo   2. Then push your code to it
echo.
echo Let's start!
echo.

REM Open GitHub to create new repo
echo [1/3] Opening GitHub in browser...
start https://github.com/new

echo.
echo [2/3] Please do the following in the browser:
echo.
echo    1. Sign in to GitHub (if not already)
echo    2. Fill in Repository name: test-manager-system
echo    3. Select Private
echo    4. Click "Create repository"
echo.
echo    DO NOT close this window!
echo.
pause

echo.
echo [3/3] Pushing code to GitHub...
echo.

REM Initialize git if not done
if not exist ".git" (
    git init
    git add .
    git commit -m "Initial commit"
)

REM Get the URL from user
echo.
echo After creating the repo, GitHub will show a URL like:
echo   https://github.com/YOUR_USERNAME/test-manager-system
echo.
echo Copy that URL and paste it here:
set /p REPO_URL=URL:

REM Extract username from URL
for /f "tokens=4 delims=/" %%a in ("%REPO_URL%") do set USER=%%a

REM Set remote and push
git remote add origin %REPO_URL%
git branch -M main
git push -u origin main

echo.
echo ========================================
echo [OK] Code pushed to GitHub!
echo.
echo Next Step: Deploy to Railway
echo.
echo 1. Open: https://railway.app
echo 2. Login with GitHub
echo 3. Click "New Project" > "Deploy from GitHub"
echo 4. Select "test-manager-system"
echo 5. Wait for deployment
echo.
echo You will get a permanent URL!
echo ========================================
pause

@echo off
chcp 65001 >nul
title 测试管理系统
echo.
echo ========================================
echo          测试管理系统 - 启动中
echo ========================================
echo.
python start.py %*

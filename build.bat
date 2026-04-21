@echo off
chcp 65001 >nul
title 测试管理系统 - 打包工具
echo.
echo ========================================
echo      测试管理系统 - 打包工具
echo ========================================
echo.

echo [1/4] 检查 PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo        安装 PyInstaller...
    pip install pyinstaller --quiet
)

echo [2/4] 安装依赖...
pip install -r requirements.txt --quiet

echo [3/4] 清理旧文件...
if exist "dist\test_manager" rd /s /q "dist\test_manager"
if exist "build" rd /s /q "build"
if exist "*.spec" del /q "*.spec"

echo [4/4] 开始打包...
echo.
pyinstaller --name "测试管理系统" ^
             --onefile ^
             --console ^
             --icon=NONE ^
             --distpath "dist" ^
             --workpath "build" ^
             --add-data "frontend;frontend" ^
             --add-data "backend/data;backend/data" ^
             --add-data "backend/test_cases;backend/test_cases" ^
             --add-data "backend/reports;backend/reports" ^
             --runtime-tmpdir "." ^
             --noconfirm ^
             start.py

echo.
echo ========================================
if exist "dist\测试管理系统.exe" (
    echo [OK] 打包完成！
    echo.
    echo 生成的文件: dist\测试管理系统.exe
    echo.
    echo 运行方式: 双击 dist\测试管理系统.exe
) else (
    echo [X] 打包失败，请检查错误信息
)
echo ========================================
pause

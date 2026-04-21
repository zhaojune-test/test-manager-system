#!/usr/bin/env python3
"""
测试管理系统 - 启动脚本
实现开箱即用：自动安装依赖、初始化环境、启动服务
"""
import os
import sys
import subprocess
import webbrowser
import time
import argparse
import json

# 确保在正确的目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"[X] Python 版本过低: {version.major}.{version.minor}.{version.micro}")
        print("    需要 Python 3.8 或更高版本")
        return False
    print(f"[OK] Python 版本: {version.major}.{version.minor}.{version.micro}")
    return True


def load_env_config():
    """加载 .env 配置文件到环境变量"""
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("    [OK] .env 配置已加载")
        return True
    else:
        print("    [!] 未找到 .env 文件，将使用默认配置")
        print("    提示: 复制 .env.example 为 .env 并配置 API Key")
        return False


def init_llm_config():
    """初始化 LLM 配置文件"""
    llm_config_path = os.path.join('backend', 'data', 'llm_config.json')

    # 如果文件存在且已有有效配置，跳过
    if os.path.exists(llm_config_path):
        with open(llm_config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            if config.get('minimax_api_key') or config.get('glm_api_key'):
                print("    [OK] LLM 配置已存在")
                return True

    # 从环境变量加载配置
    minimax_key = os.environ.get('MINIMAX_API_KEY', '')
    minimax_group = os.environ.get('MINIMAX_GROUP_ID', '')
    glm_key = os.environ.get('GLM_API_KEY', '')
    default_provider = os.environ.get('DEFAULT_LLM_PROVIDER', 'minimax')

    config = {
        "minimax_api_key": minimax_key,
        "minimax_group_id": minimax_group,
        "glm_api_key": glm_key,
        "default_provider": default_provider,
        "updated_at": ""
    }

    os.makedirs(os.path.dirname(llm_config_path), exist_ok=True)
    with open(llm_config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    if minimax_key or glm_key:
        print("    [OK] LLM 配置已从环境变量加载")
    else:
        print("    [!] LLM API Key 未配置，部分功能可能受限")
        print("    提示: 请在 .env 文件或 backend/data/llm_config.json 中配置")

    return True


def get_pip_version():
    """获取 pip 版本"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True, text=True
        )
        return result.stdout.strip()
    except:
        return "未知"


def install_requirements(silent=False):
    """安装 Python 依赖"""
    print("\n[*] 正在安装 Python 依赖...")

    pip_version = get_pip_version()
    if not silent:
        print(f"    {pip_version}")

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"],
            stdout=subprocess.DEVNULL if silent else None,
            stderr=subprocess.STDOUT
        )
        print("    [OK] 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"    [X] 依赖安装失败: {e}")
        return False


def install_playwright(silent=False):
    """安装 Playwright 浏览器"""
    print("\n[*] 正在安装 Playwright 浏览器...")

    # 检查 playwright 是否已安装
    playwright_installed = False
    try:
        subprocess.run(
            [sys.executable, "-c", "import playwright"],
            capture_output=True, check=True
        )
        playwright_installed = True
        print("    [OK] Playwright 包已安装")
    except:
        print("    正在安装 playwright 包...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "playwright", "--quiet"],
                stdout=subprocess.DEVNULL if silent else None
            )
            playwright_installed = True
            print("    [OK] Playwright 包安装完成")
        except subprocess.CalledProcessError:
            print("    [!] Playwright 包安装失败，将跳过浏览器安装")
            return True

    # 检查 Chromium 是否已安装
    if playwright_installed:
        try:
            # 直接运行 install 命令，通过返回码判断是否需要安装
            result = subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                print("    [OK] Chromium 浏览器已就绪")
                return True
        except subprocess.TimeoutExpired:
            # 超时说明正在安装中
            print("    [*] Chromium 正在安装中...")
            return True
        except Exception as e:
            pass

    print("    [!] Chromium 浏览器安装失败，截图功能可能不可用")
    return True


def init_environment():
    """初始化环境"""
    print("\n[*] 正在初始化环境...")

    # 创建必要目录
    dirs = [
        'backend/data',
        'backend/test_cases',
        'backend/reports',
        'reports',
        'logs'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # 初始化空数据文件
    for f in ['testcases.json', 'test_results.json']:
        path = os.path.join('backend/data', f)
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as file:
                file.write('[]')

    print("    [OK] 环境初始化完成")
    return True


def check_port(port=5000):
    """检查端口是否被占用"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result != 0


def start_server(silent=False):
    """启动后端服务"""
    if not check_port(5000):
        print("\n[!] 端口 5000 已被占用，后端服务可能已在运行")
        return True

    print("\n[*] 正在启动后端服务...")

    try:
        process = subprocess.Popen(
            [sys.executable, "backend/server.py"],
            stdout=subprocess.DEVNULL if silent else None,
            stderr=subprocess.DEVNULL if silent else None
        )
        time.sleep(2)

        if process.poll() is None:
            print("    [OK] 后端服务已启动: http://localhost:5000")
            return True
        else:
            print("    [X] 后端服务启动失败")
            return False
    except Exception as e:
        print(f"    [X] 后端服务启动异常: {e}")
        return False


def open_browser():
    """打开浏览器"""
    print("\n[*] 正在打开浏览器...")
    time.sleep(1)
    webbrowser.open('http://localhost:5000/')


def main():
    parser = argparse.ArgumentParser(description='测试管理系统启动脚本')
    parser.add_argument('--silent', '-s', action='store_true', help='静默模式，不打开浏览器')
    parser.add_argument('--skip-playwright', action='store_true', help='跳过 Playwright 安装')
    parser.add_argument('--check', '-c', action='store_true', help='仅检查环境')
    args = parser.parse_args()

    print("=" * 50)
    print("        测试管理系统 - 开箱即用启动")
    print("=" * 50)

    # 环境检查
    print("\n[*] 环境检查...")
    if not check_python_version():
        input("\n按回车键退出...")
        sys.exit(1)

    # 加载环境变量配置
    load_env_config()

    # 初始化 LLM 配置
    init_llm_config()

    if args.check:
        print("\n[OK] 环境检查通过")
        sys.exit(0)

    # 安装依赖
    if not install_requirements(args.silent):
        input("\n按回车键退出...")
        sys.exit(1)

    # 安装 Playwright
    if not args.skip_playwright:
        install_playwright(args.silent)

    # 初始化环境
    if not init_environment():
        input("\n按回车键退出...")
        sys.exit(1)

    # 启动服务
    if not start_server(args.silent):
        input("\n按回车键退出...")
        sys.exit(1)

    # 打开浏览器
    if not args.silent:
        open_browser()

    print("\n" + "=" * 50)
    print("[OK] 系统已启动！")
    print("     - 后端服务: http://localhost:5000")
    print("     - 前端页面: http://localhost:5000/")
    print("=" * 50)

    if not args.silent:
        print("\n按 Ctrl+C 停止服务\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n[!] 服务已停止")
    else:
        print("     (静默模式，服务已在后台运行)\n")


if __name__ == '__main__':
    main()

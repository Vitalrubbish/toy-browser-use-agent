#!/usr/bin/env python3
"""
Web Agent 快速启动脚本
自动检查依赖、启动服务、打开浏览器
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path


class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.END}\n")


def print_success(text):
    """打印成功信息"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    """打印错误信息"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text):
    """打印警告信息"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text):
    """打印信息"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")


def check_python_version():
    """检查 Python 版本"""
    print_info("检查 Python 版本...")
    version = sys.version_info
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print_error(f"需要 Python 3.7+, 当前版本: {version.major}.{version.minor}")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_dependencies():
    """检查并安装依赖"""
    print_info("检查依赖包...")
    
    required_packages = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS'
    }
    
    missing_packages = []
    
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
            print_success(f"{package_name} 已安装")
        except ImportError:
            missing_packages.append(package_name)
            print_warning(f"{package_name} 未安装")
    
    if missing_packages:
        print_info(f"安装缺失的包: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                *missing_packages, '--quiet'
            ])
            print_success("依赖安装完成")
        except subprocess.CalledProcessError:
            print_error("依赖安装失败")
            return False
    
    return True


def find_free_port(start_port=5000, max_tries=10):
    """找到可用端口"""
    import socket
    
    for port in range(start_port, start_port + max_tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    
    return None


def start_api_server(port=5000):
    """启动 API 服务器"""
    print_info(f"启动 API 服务器 (端口 {port})...")
    
    script_path = Path(__file__).parent / 'api_server.py'
    
    if not script_path.exists():
        print_error(f"找不到 api_server.py")
        return None
    
    try:
        # 设置环境变量
        env = os.environ.copy()
        env['FLASK_PORT'] = str(port)
        
        # 启动服务器进程
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待服务器启动
        time.sleep(2)
        
        if process.poll() is not None:
            print_error("服务器启动失败")
            return None
        
        print_success(f"API 服务器运行在 http://localhost:{port}")
        return process
        
    except Exception as e:
        print_error(f"启动服务器时出错: {e}")
        return None


def start_http_server(port=8080):
    """启动简单的 HTTP 服务器"""
    print_info(f"启动前端服务器 (端口 {port})...")
    
    try:
        process = subprocess.Popen(
            [sys.executable, '-m', 'http.server', str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        time.sleep(1)
        
        if process.poll() is not None:
            print_error("前端服务器启动失败")
            return None
        
        print_success(f"前端服务器运行在 http://localhost:{port}")
        return process
        
    except Exception as e:
        print_error(f"启动前端服务器时出错: {e}")
        return None


def open_browser(url, delay=2):
    """打开浏览器"""
    print_info(f"等待 {delay} 秒后打开浏览器...")
    time.sleep(delay)
    
    try:
        webbrowser.open(url)
        print_success(f"已在浏览器中打开: {url}")
    except Exception as e:
        print_warning(f"无法自动打开浏览器: {e}")
        print_info(f"请手动访问: {url}")


def main():
    """主函数"""
    print_header("Web Agent 启动器")
    
    # 检查 Python 版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 找到可用端口
    api_port = find_free_port(5000)
    frontend_port = find_free_port(8080)
    
    if not api_port or not frontend_port:
        print_error("无法找到可用端口")
        sys.exit(1)
    
    # 启动 API 服务器
    api_process = start_api_server(api_port)
    if not api_process:
        print_error("API 服务器启动失败")
        sys.exit(1)
    
    # 启动前端服务器
    frontend_process = start_http_server(frontend_port)
    if not frontend_process:
        print_warning("前端服务器启动失败,尝试直接打开 HTML 文件")
        frontend_url = f"file://{Path(__file__).parent / 'index.html'}"
    else:
        frontend_url = f"http://localhost:{frontend_port}/index.html"
    
    # 打开浏览器
    open_browser(frontend_url)
    
    # 显示状态
    print_header("服务状态")
    print_info(f"API 服务器: http://localhost:{api_port}")
    print_info(f"前端界面: {frontend_url}")
    print_info(f"健康检查: http://localhost:{api_port}/api/health")
    print()
    print_warning("按 Ctrl+C 停止所有服务")
    
    try:
        # 保持运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print_header("关闭服务")
        
        if api_process:
            print_info("停止 API 服务器...")
            api_process.terminate()
            api_process.wait()
        
        if frontend_process:
            print_info("停止前端服务器...")
            frontend_process.terminate()
            frontend_process.wait()
        
        print_success("所有服务已停止")
        print()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print_error(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

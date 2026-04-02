#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

def build_frontend():
    """构建前端"""
    print("开始构建前端...")
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    
    # 安装依赖
    subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
    
    # 构建
    subprocess.run(['npm', 'run', 'build'], cwd=frontend_dir, check=True)
    
    print("前端构建完成")

def build_backend():
    """打包后端"""
    print("准备后端文件...")
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    dist_dir = os.path.join(os.path.dirname(__file__), 'dist')
    
    # 创建dist目录
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)
    
    # 复制后端文件
    backend_files = ['app.py', 'database.py', 'ssh_manager.py', 'log_handlers.py', 'requirements.txt']
    for file in backend_files:
        src = os.path.join(backend_dir, file)
        dst = os.path.join(dist_dir, file)
        if os.path.exists(src):
            shutil.copy2(src, dst)
    
    # 复制前端构建文件
    frontend_dist = os.path.join(backend_dir, '..', 'frontend', 'dist')
    if os.path.exists(frontend_dist):
        shutil.copytree(frontend_dist, os.path.join(dist_dir, 'static'))
    
    print(f"打包完成，输出目录: {dist_dir}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--no-frontend':
        build_backend()
    else:
        build_frontend()
        build_backend()
    
    print("构建完成！")
    print("运行方式:")
    print("  cd dist")
    print("  pip install -r requirements.txt")
    print("  python app.py")
    print("或使用:")
    print("  uvicorn app:app --host 0.0.0.0 --port 60501")

if __name__ == '__main__':
    main()
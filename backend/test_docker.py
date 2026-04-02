#!/usr/bin/env python3
import paramiko
import time

# SSH 配置（替换为你的实际主机信息）
host = "139.196.204.133"
port = 22
username = "root"
password = "20599Tommy"  # 替换为实际密码

def test_docker_containers():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"连接到 {host}:{port}")
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        print("SSH 连接成功")
        
        # 测试 Docker 命令
        print("\n测试 Docker 命令...")
        
        # 测试 docker ps
        command = "docker ps --format 'table {{.Names}}\t{{.ID}}\t{{.Status}}\t{{.Image}}'"
        print(f"执行命令: {command}")
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        print(f"输出:\n{output}")
        if error:
            print(f"错误:\n{error}")
        
        # 测试 Docker 是否安装
        print("\n测试 Docker 是否安装...")
        stdin, stdout, stderr = client.exec_command("which docker")
        docker_path = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"Docker 路径: {docker_path}")
        
        if not docker_path:
            print("Docker 未安装或不在 PATH 中")
        
        # 测试 Docker 版本
        print("\n测试 Docker 版本...")
        stdin, stdout, stderr = client.exec_command("docker --version")
        version = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"Docker 版本: {version}")
        
        client.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_docker_containers()
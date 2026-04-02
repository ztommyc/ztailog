#!/usr/bin/env python3
import paramiko
import time

# SSH 配置
host = "139.196.204.133"  # 替换为实际的主机
port = 22
username = "root"
password = "20599Tommy"  # 替换为实际的密码

def test_ssh():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"连接到 {host}:{port}")
        client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        print("SSH 连接成功")
        
        # 测试执行命令
        print("\n测试执行 tail 命令...")
        channel = client.get_transport().open_session()
        channel.exec_command("tail -10 /var/log/messages")
        
        # 读取输出
        while True:
            if channel.recv_ready():
                data = channel.recv(1024).decode('utf-8')
                if data:
                    print(f"收到数据: {data}")
                else:
                    break
            if channel.exit_status_ready():
                print(f"命令退出状态: {channel.recv_exit_status()}")
                break
            time.sleep(0.1)
        
        print("\n测试实时跟踪...")
        channel2 = client.get_transport().open_session()
        channel2.exec_command("tail -f /var/log/messages")
        
        # 读取几行数据
        for i in range(5):
            if channel2.recv_ready():
                data = channel2.recv(1024).decode('utf-8')
                if data:
                    print(f"实时数据 {i+1}: {data[:100]}")
            time.sleep(2)
        
        channel2.close()
        client.close()
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_ssh()
import paramiko
import asyncio
import threading
import queue
from typing import Optional, Dict, List
import io

class SSHConnection:
    def __init__(self, host: str, port: int, username: str, password: str = None, private_key: str = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.private_key = private_key
        self.client: Optional[paramiko.SSHClient] = None
        self.active_channels: Dict[str, paramiko.Channel] = {}
        
    def connect(self):
        """建立SSH连接"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                'hostname': self.host,
                'port': self.port,
                'username': self.username,
                'timeout': 10
            }
            
            if self.password:
                connect_kwargs['password'] = self.password
            elif self.private_key:
                key = paramiko.RSAKey.from_private_key(io.StringIO(self.private_key))
                connect_kwargs['pkey'] = key
            
            self.client.connect(**connect_kwargs)
            return True
        except Exception as e:
            print(f"SSH连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开SSH连接"""
        for channel in self.active_channels.values():
            try:
                channel.close()
            except:
                pass
        if self.client:
            self.client.close()
    
    def execute_command(self, command: str, timeout: int = 30):
        """执行命令并返回输出"""
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            return output, error
        except Exception as e:
            return None, str(e)
    
    def get_docker_containers(self):
        """获取Docker容器列表"""
        # 使用更简单的命令格式
        command = "docker ps -a --format '{{.Names}}|{{.ID}}|{{.Status}}|{{.Image}}'"
        output, error = self.execute_command(command)
        print(f"Docker 命令输出: {output}")  # 调试输出
        print(f"Docker 命令错误: {error}")  # 调试输出
        
        if output:
            containers = []
            lines = output.strip().split('\n')
            for line in lines:
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 4:
                        # 排除 k8s 容器（通常名称包含 k8s_）
                        if 'k8s_' not in parts[0]:
                            containers.append({
                                'name': parts[0],
                                'id': parts[1],
                                'status': parts[2],
                                'image': parts[3]
                            })
            print(f"解析到的容器: {containers}")  # 调试输出
            return containers
        return []
    
    def get_podman_containers(self):
        """获取Podman容器列表"""
        command = "podman ps --format 'table {{.Names}}|{{.ID}}|{{.Status}}|{{.Image}}'"
        output, error = self.execute_command(command)
        if output:
            lines = output.strip().split('\n')
            containers = []
            for line in lines[1:]:
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 2:
                        containers.append({
                            'name': parts[0],
                            'id': parts[1],
                            'status': parts[2] if len(parts) > 2 else '',
                            'image': parts[3] if len(parts) > 3 else ''
                        })
            return containers
        return []
    
    def get_k8s_namespaces(self):
        """获取K8s命名空间"""
        command = "kubectl get namespaces -o jsonpath='{.items[*].metadata.name}'"
        output, error = self.execute_command(command)
        if output:
            return output.strip().split()
        return ['default']
    
    def get_k8s_pods(self, namespace='default'):
        """获取K8s Pod列表（包含状态和年龄）"""
        # 使用默认格式，kubectl 会自动显示友好的 AGE（如 5d, 2h, 30m）
        command = f"kubectl -n {namespace} get pods --no-headers"
        output, error = self.execute_command(command)
        
        pods = []
        if output:
            lines = output.strip().split('\n')
            for line in lines:
                if line.strip():
                    parts = line.split()
                    # kubectl get pods 默认输出: NAME READY STATUS RESTARTS AGE
                    if len(parts) >= 5:
                        pods.append({
                            'name': parts[0],
                            'status': parts[2],  # STATUS 列
                            'age': parts[4]      # AGE 列（已经是友好格式，如 13d, 2h, 5m）
                        })
                    elif len(parts) >= 3:
                        pods.append({
                            'name': parts[0],
                            'status': parts[2] if len(parts) > 2 else 'Unknown',
                            'age': parts[4] if len(parts) > 4 else '-'
                        })
        return pods
    
    def tail_log(self, log_path: str, lines: int = 100, channel_id: str = None):
        """实时跟踪文件日志"""
        # 使用 tail -f 命令，并确保使用正确的参数
        command = f"tail -n {lines} -f {log_path}"
        print(f"执行命令: {command}")
        return self._tail_command(command, channel_id)
    
    def tail_docker_logs(self, container_name: str, lines: int = 100, channel_id: str = None):
        """查看Docker日志（自动判断实时或历史）"""
        # 检查容器状态
        status_cmd = f"docker inspect -f '{{{{.State.Status}}}}' {container_name}"
        status_output, _ = self.execute_command(status_cmd)
        status = status_output.strip() if status_output else ''
        
        print(f"容器 {container_name} 状态: {status}")
        
        if status in ['exited', 'dead', 'created', 'stopped']:
            # 已停止的容器，只获取历史日志，不使用 -f
            command = f"docker logs --tail={lines} {container_name}"
            print(f"使用历史日志命令: {command}")
        else:
            # 运行中的容器，实时跟踪
            command = f"docker logs -f --tail={lines} {container_name}"
            print(f"使用实时跟踪命令: {command}")
			
        test_output, test_error = self.execute_command(f"{command} 2>&1 | head -5")
        print(f"测试命令输出: {test_output[:200] if test_output else '无'}")
        print(f"测试命令错误: {test_error[:200] if test_error else '无'}")        
		
        return self._tail_command(command, channel_id)

    
    def tail_podman_logs(self, container_name: str, lines: int = 100, channel_id: str = None):
        """实时跟踪Podman日志（支持已停止的容器）"""
        # 检查容器状态
        status_cmd = f"podman inspect -f '{{{{.State.Status}}}}' {container_name}"
        status_output, _ = self.execute_command(status_cmd)
        status = status_output.strip() if status_output else ''
        
        if status in ['exited', 'stopped']:
            command = f"podman logs --tail={lines} {container_name}"
        else:
            command = f"podman logs -f --tail={lines} {container_name}"
        
        return self._tail_command(command, channel_id)
    
    def tail_k8s_logs(self, namespace: str, pod_name: str, lines: int = 100, channel_id: str = None):
        """查看K8s日志（支持已停止的Pod）"""
        # K8s 可以使用 --previous 查看已停止容器的日志
        # 先检查 Pod 状态
        status_cmd = f"kubectl -n {namespace} get pod {pod_name} -o jsonpath='{{.status.phase}}'"
        status_output, _ = self.execute_command(status_cmd)
        status = status_output.strip() if status_output else ''
        
        if status in ['Failed', 'Succeeded']:
            # 已停止的 Pod，使用 --previous 查看之前容器的日志
            command = f"kubectl -n {namespace} logs --previous --tail={lines} {pod_name}"
        else:
            # 运行中的 Pod，实时跟踪
            command = f"kubectl -n {namespace} logs -f --tail={lines} {pod_name}"
        
        return self._tail_command(command, channel_id)
    
    def _tail_command(self, command: str, channel_id: str = None):
        """执行tail命令并返回channel"""
        try:
            print(f"执行命令: {command}")
            channel = self.client.get_transport().open_session()
            # 设置更大的窗口大小以获得更好的性能
            channel.get_pty()
            channel.exec_command(command)
            
            if channel_id:
                self.active_channels[channel_id] = channel
            
            return channel
        except Exception as e:
            print(f"执行命令失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def download_file(self, file_path: str):
        """下载完整文件"""
        try:
            sftp = self.client.open_sftp()
            remote_file = sftp.open(file_path, 'r')
            content = remote_file.read().decode('utf-8', errors='ignore')
            remote_file.close()
            sftp.close()
            return content
        except Exception as e:
            return None


    def is_text_file(self, file_path: str) -> bool:
        """检测文件是否为文本文件"""
        try:
            # 使用 file 命令检测文件类型
            command = f"file -b --mime-type {file_path}"
            output, error = self.execute_command(command)
            
            if output:
                mime_type = output.strip()
                # 文本文件的 MIME 类型
                text_types = [
                    'text/plain',
                    'text/x-log',
                    'text/x-shellscript',
                    'text/x-python',
                    'text/x-c',
                    'application/json',
                    'application/xml',
                    'text/x-yaml',
                    'text/x-properties',
                    'inode/x-empty'  # 空文件
                ]
                
                # 检查是否是文本类型
                for text_type in text_types:
                    if text_type in mime_type:
                        return True
                
                # 如果 MIME 类型以 text/ 开头，也是文本文件
                if mime_type.startswith('text/'):
                    return True
                
                # 如果不是文本文件
                print(f"文件 {file_path} 不是文本文件，MIME类型: {mime_type}")
                return False
                
        except Exception as e:
            print(f"检测文件类型失败: {e}")
            return False
        
        return False
    
    def get_file_size(self, file_path: str) -> int:
        """获取文件大小（字节）"""
        try:
            command = f"stat -c%s {file_path} 2>/dev/null || stat -f%z {file_path} 2>/dev/null"
            output, error = self.execute_command(command)
            if output and output.strip().isdigit():
                return int(output.strip())
        except Exception as e:
            print(f"获取文件大小失败: {e}")
        return 0


class SSHManager:
    _instances = {}
    
    @classmethod
    def get_connection(cls, host_id: int, host_config: dict):
        """获取或创建SSH连接"""
        if host_id not in cls._instances:
            conn = SSHConnection(
                host=host_config['host'],
                port=host_config['port'],
                username=host_config['username'],
                password=host_config.get('password'),
                private_key=host_config.get('private_key')
            )
            if conn.connect():
                cls._instances[host_id] = conn
            else:
                return None
        return cls._instances[host_id]
    
    @classmethod
    def close_connection(cls, host_id: int):
        """关闭SSH连接"""
        if host_id in cls._instances:
            cls._instances[host_id].disconnect()
            del cls._instances[host_id]
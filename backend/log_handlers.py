import json
import threading
import time
import asyncio
from typing import Dict, Set
from collections import defaultdict

class LogStreamManager:
    def __init__(self):
        self.active_streams: Dict[str, Dict] = {}
        self.websocket_connections: Dict[str, Set] = {}
        self.loop = None  # 存储事件循环
    
    def set_event_loop(self, loop):
        """设置事件循环"""
        self.loop = loop
    
    def add_stream(self, stream_id: str, ssh_conn, channel, log_type: str, config: dict):
        """添加日志流"""
        self.active_streams[stream_id] = {
            'ssh_conn': ssh_conn,
            'channel': channel,
            'log_type': log_type,
            'config': config,
            'running': True
        }
        
        # 启动读取线程
        thread = threading.Thread(target=self._read_stream, args=(stream_id,))
        thread.daemon = True
        thread.start()
    
    def _read_stream(self, stream_id: str):
        """读取流输出"""
        stream_info = self.active_streams.get(stream_id)
        if not stream_info:
            return
        
        channel = stream_info['channel']
        print(f"开始读取流: {stream_id}")
        
        timeout_counter = 0
        
        while stream_info['running']:
            try:
                # 检查是否有数据可读
                if channel.recv_ready():
                    data = channel.recv(1024).decode('utf-8', errors='ignore')
                    if data:
                        print(f"收到数据: {len(data)} 字节")
                        self._broadcast_log(stream_id, data)
                        timeout_counter = 0
                    else:
                        print("收到空数据")
                else:
                    # 如果没有数据，短暂等待
                    time.sleep(0.1)
                    timeout_counter += 1
                    
                    # 每10秒发送一个心跳，保持连接
                    if timeout_counter >= 100:  # 10秒
                        self._broadcast_heartbeat(stream_id)
                        timeout_counter = 0
                
                # 检查通道是否关闭
                if channel.exit_status_ready():
                    status = channel.recv_exit_status()
                    print(f"通道关闭，退出状态: {status}")
                    
                    # 对于已停止的容器，正常退出后不需要报错
                    if status != 0:
                        error_msg = f"命令执行失败，退出状态: {status}"
                        self._broadcast_error(stream_id, error_msg)
                    # 通知前端日志流已结束
                    data = channel.recv(-1).decode('utf-8', errors='ignore')
                    data += "\n[日志流已结束 - 容器已停止]\n"
                    self._broadcast_log(stream_id, data)
                    # 延迟关闭，让前端有时间显示最后的日志
                    time.sleep(1)
                    break
                    
            except Exception as e:
                print(f"读取流错误: {e}")
                self._broadcast_error(stream_id, str(e))
                break
        
        self.remove_stream(stream_id)
    def _broadcast_log(self, stream_id: str, data: str):
        """广播日志数据 - 使用事件循环发送"""
        if stream_id in self.websocket_connections and self.loop:
            message = json.dumps({
                'type': 'log',
                'stream_id': stream_id,
                'data': data
            })
            
            to_remove = []
            for ws in self.websocket_connections[stream_id]:
                try:
                    # 在事件循环中运行协程
                    asyncio.run_coroutine_threadsafe(
                        ws.send_text(message),
                        self.loop
                    )
                except Exception as e:
                    print(f"广播失败: {e}")
                    to_remove.append(ws)
            
            # 移除失效的连接
            for ws in to_remove:
                self.websocket_connections[stream_id].discard(ws)
    
    def _broadcast_heartbeat(self, stream_id: str):
        """发送心跳保持连接"""
        if stream_id in self.websocket_connections and self.loop:
            message = json.dumps({
                'type': 'heartbeat',
                'stream_id': stream_id,
                'timestamp': time.time()
            })
            to_remove = []
            for ws in self.websocket_connections[stream_id]:
                try:
                    asyncio.run_coroutine_threadsafe(
                        ws.send_text(message),
                        self.loop
                    )
                except:
                    to_remove.append(ws)
            
            for ws in to_remove:
                self.websocket_connections[stream_id].discard(ws)
    
    def _broadcast_error(self, stream_id: str, error: str):
        """广播错误信息"""
        if stream_id in self.websocket_connections and self.loop:
            message = json.dumps({
                'type': 'error',
                'stream_id': stream_id,
                'message': error
            })
            to_remove = []
            for ws in self.websocket_connections[stream_id]:
                try:
                    asyncio.run_coroutine_threadsafe(
                        ws.send_text(message),
                        self.loop
                    )
                except:
                    to_remove.append(ws)
            
            for ws in to_remove:
                self.websocket_connections[stream_id].discard(ws)
    
    def remove_stream(self, stream_id: str):
        """移除流"""
        if stream_id in self.active_streams:
            stream_info = self.active_streams[stream_id]
            stream_info['running'] = False
            try:
                stream_info['channel'].close()
            except:
                pass
            del self.active_streams[stream_id]
        
        if stream_id in self.websocket_connections:
            del self.websocket_connections[stream_id]
    
    def add_websocket(self, stream_id: str, websocket):
        """添加WebSocket连接"""
        if stream_id not in self.websocket_connections:
            self.websocket_connections[stream_id] = set()
        self.websocket_connections[stream_id].add(websocket)
    
    def remove_websocket(self, stream_id: str, websocket):
        """移除WebSocket连接"""
        if stream_id in self.websocket_connections:
            self.websocket_connections[stream_id].discard(websocket)
            if not self.websocket_connections[stream_id]:
                self.remove_stream(stream_id)

stream_manager = LogStreamManager()
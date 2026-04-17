from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import asyncio
import json
import os
import sys
import io
import zipfile

from database import SessionLocal, SSHHost, LogConfig, LogPathHistory, init_db
from ssh_manager import SSHManager
from log_handlers import stream_manager
import uuid
from datetime import datetime
# ==================== 配置 ====================
CONTEXT_PATH = "/ztailog"

# ==================== 路径配置 ====================
def get_base_dir():
    """获取程序运行时的基础目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_static_dir():
    """获取静态文件目录"""
    base_dir = get_base_dir()
    
    local_static = os.path.join(base_dir, 'static')
    if os.path.exists(local_static):
        return local_static
    
    if hasattr(sys, '_MEIPASS'):
        meipass_static = os.path.join(sys._MEIPASS, 'static')
        if os.path.exists(meipass_static):
            return meipass_static
    
    dev_static = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'dist')
    if os.path.exists(dev_static):
        return dev_static
    
    return None

BASE_DIR = get_base_dir()
STATIC_DIR = get_static_dir()
DB_PATH = os.path.join(BASE_DIR, 'ztailog.db')

print(f"BASE_DIR: {BASE_DIR}")
print(f"STATIC_DIR: {STATIC_DIR}")
print(f"DB_PATH: {DB_PATH}")
print(f"CONTEXT_PATH: {CONTEXT_PATH}")

# ==================== FastAPI 应用 ====================
app = FastAPI(title="Ztailog - 日志可视化平台")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
init_db()

# ==================== Pydantic模型 ====================
class HostCreate(BaseModel):
    name: str
    host: str
    port: int = 22
    username: str
    password: Optional[str] = None
    private_key: Optional[str] = None

class LogPathHistoryItem(BaseModel):
    id: int
    log_path: str
    last_used: str
    use_count: int

class HostUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    private_key: Optional[str] = None

class LogConfigUpdate(BaseModel):
    default_lines: int = 100

# ==================== API路由 ====================
@app.get(CONTEXT_PATH + "/api/hosts")
async def get_hosts():
    """获取所有SSH主机"""
    db = SessionLocal()
    try:
        hosts = db.query(SSHHost).filter(SSHHost.is_deleted == False).all()
        return [
            {
                "id": h.id,
                "name": h.name,
                "host": h.host,
                "port": h.port,
                "username": h.username,
                "created_at": h.created_at.isoformat() if h.created_at else None
            }
            for h in hosts
        ]
    finally:
        db.close()

@app.get(CONTEXT_PATH + "/api/hosts/{host_id}")
async def get_host(host_id: int):
    """获取单个主机详情"""
    db = SessionLocal()
    try:
        host = db.query(SSHHost).filter(
            SSHHost.id == host_id,
            SSHHost.is_deleted == False
        ).first()
        if not host:
            raise HTTPException(status_code=404, detail="主机不存在")
        return {
            "id": host.id,
            "name": host.name,
            "host": host.host,
            "port": host.port,
            "username": host.username,
            "created_at": host.created_at.isoformat() if host.created_at else None
        }
    finally:
        db.close()

@app.post(CONTEXT_PATH + "/api/hosts")
async def create_host(host: HostCreate):
    """创建SSH主机"""
    db = SessionLocal()
    try:
        db_host = SSHHost(
            name=host.name,
            host=host.host,
            port=host.port,
            username=host.username,
            password=host.password,
            private_key=host.private_key
        )
        db.add(db_host)
        db.commit()
        db.refresh(db_host)
        
        # 创建默认日志配置
        for log_type in ['file', 'docker', 'podman', 'k8s']:
            config = LogConfig(
                host_id=db_host.id,
                log_type=log_type,
                default_lines=100
            )
            db.add(config)
        db.commit()
        
        return {"id": db_host.id, "message": "主机创建成功"}
    finally:
        db.close()

@app.post(CONTEXT_PATH + "/api/hosts/{host_id}")
async def update_host(host_id: int, host: HostUpdate, action: str = "update"):
    """更新SSH主机"""
    if action != "update":
        raise HTTPException(status_code=400, detail="无效的操作类型")
    db = SessionLocal()
    try:
        db_host = db.query(SSHHost).filter(
            SSHHost.id == host_id,
            SSHHost.is_deleted == False
        ).first()
        if not db_host:
            raise HTTPException(status_code=404, detail="主机不存在")
        
        for key, value in host.dict(exclude_unset=True).items():
            setattr(db_host, key, value)
        
        db_host.updated_at = datetime.utcnow()
        db.commit()
        return {"message": "主机更新成功"}
    finally:
        db.close()

@app.post(CONTEXT_PATH + "/api/hosts/{host_id}/delete")
async def delete_host(host_id: int):
    """逻辑删除SSH主机"""
    db = SessionLocal()
    try:
        db_host = db.query(SSHHost).filter(
            SSHHost.id == host_id,
            SSHHost.is_deleted == False
        ).first()
        if not db_host:
            raise HTTPException(status_code=404, detail="主机不存在")
        
        # 逻辑删除主机
        db_host.is_deleted = True
        db_host.deleted_at = datetime.utcnow()
        
        # 同时逻辑删除关联的配置和历史
        db.query(LogConfig).filter(
            LogConfig.host_id == host_id,
            LogConfig.is_deleted == False
        ).update({
            LogConfig.is_deleted: True,
            LogConfig.deleted_at: datetime.utcnow()
        })
        
        db.query(LogPathHistory).filter(
            LogPathHistory.host_id == host_id,
            LogPathHistory.is_deleted == False
        ).update({
            LogPathHistory.is_deleted: True,
            LogPathHistory.deleted_at: datetime.utcnow()
        })
        
        db.commit()
        
        # 关闭SSH连接
        SSHManager.close_connection(host_id)
        
        return {"message": "主机删除成功"}
    except Exception as e:
        db.rollback()
        print(f"删除主机错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get(CONTEXT_PATH + "/api/hosts/{host_id}/log-config")
async def get_log_config(host_id: int):
    """获取日志配置（只查未删除的）"""
    db = SessionLocal()
    try:
        # 先检查主机是否存在且未删除
        host = db.query(SSHHost).filter(
            SSHHost.id == host_id,
            SSHHost.is_deleted == False
        ).first()
        if not host:
            raise HTTPException(status_code=404, detail="主机不存在")
        
        configs = db.query(LogConfig).filter(
            LogConfig.host_id == host_id,
            LogConfig.is_deleted == False
        ).all()
        return {
            config.log_type: config.default_lines for config in configs
        }
    finally:
        db.close()

@app.post(CONTEXT_PATH + "/api/hosts/{host_id}/log-config/{log_type}")
async def update_log_config(host_id: int, log_type: str, config: LogConfigUpdate):
    """更新日志配置"""
    db = SessionLocal()
    try:
        # 检查主机是否存在且未删除
        host = db.query(SSHHost).filter(
            SSHHost.id == host_id,
            SSHHost.is_deleted == False
        ).first()
        if not host:
            raise HTTPException(status_code=404, detail="主机不存在")
        
        db_config = db.query(LogConfig).filter(
            LogConfig.host_id == host_id,
            LogConfig.log_type == log_type,
            LogConfig.is_deleted == False
        ).first()
        
        if db_config:
            db_config.default_lines = config.default_lines
        else:
            db_config = LogConfig(
                host_id=host_id,
                log_type=log_type,
                default_lines=config.default_lines
            )
            db.add(db_config)
        
        db.commit()
        return {"message": "配置更新成功"}
    finally:
        db.close()

@app.get(CONTEXT_PATH + "/api/hosts/{host_id}/containers/{container_type}")
async def get_containers(host_id: int, container_type: str):
    """获取容器列表"""
    db = SessionLocal()
    try:
        host = db.query(SSHHost).filter(
            SSHHost.id == host_id,
            SSHHost.is_deleted == False
        ).first()
        if not host:
            raise HTTPException(status_code=404, detail="主机不存在")
        
        print(f"获取容器列表: host_id={host_id}, container_type={container_type}")
        
        ssh_conn = SSHManager.get_connection(host_id, {
            'host': host.host,
            'port': host.port,
            'username': host.username,
            'password': host.password,
            'private_key': host.private_key
        })
        
        if not ssh_conn:
            raise HTTPException(status_code=500, detail="SSH连接失败")
        
        if container_type == 'docker':
            containers = ssh_conn.get_docker_containers()
            print(f"Docker 容器数量: {len(containers)}")
        elif container_type == 'podman':
            containers = ssh_conn.get_podman_containers()
        elif container_type == 'k8s':
            namespaces = ssh_conn.get_k8s_namespaces()
            containers = {}
            for ns in namespaces:
                pods = ssh_conn.get_k8s_pods(ns)
                containers[ns] = pods
            return containers
        else:
            raise HTTPException(status_code=400, detail="不支持的容器类型")
        
        return containers
    except Exception as e:
        print(f"获取容器列表错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get(CONTEXT_PATH + "/api/hosts/{host_id}/files")
async def get_files(host_id: int, path: str = "/"):
    """获取文件列表"""
    db = SessionLocal()
    try:
        host = db.query(SSHHost).filter(SSHHost.id == host_id).first()
        if not host:
            raise HTTPException(status_code=404, detail="主机不存在")
        
        ssh_conn = SSHManager.get_connection(host_id, {
            'host': host.host,
            'port': host.port,
            'username': host.username,
            'password': host.password,
            'private_key': host.private_key
        })
        
        if not ssh_conn:
            raise HTTPException(status_code=500, detail="SSH连接失败")
        
        command = f"ls -la {path}"
        output, error = ssh_conn.execute_command(command)
        if error:
            raise HTTPException(status_code=500, detail=error)
        
        return {"files": output}
    finally:
        db.close()

@app.get(CONTEXT_PATH + "/api/hosts/{host_id}/download")
async def download_file(host_id: int, file_path: str):
    """下载完整文件（大于3M自动压缩）"""
    db = SessionLocal()
    try:
        host = db.query(SSHHost).filter(SSHHost.id == host_id).first()
        if not host:
            raise HTTPException(status_code=404, detail="主机不存在")
        
        ssh_conn = SSHManager.get_connection(host_id, {
            'host': host.host,
            'port': host.port,
            'username': host.username,
            'password': host.password,
            'private_key': host.private_key
        })
        
        if not ssh_conn:
            raise HTTPException(status_code=500, detail="SSH连接失败")
        
        # 先获取文件大小
        size_cmd = f"stat -c%s {file_path} 2>/dev/null || stat -f%z {file_path} 2>/dev/null"
        size_output, size_error = ssh_conn.execute_command(size_cmd)
        
        file_size = 0
        if size_output and size_output.strip().isdigit():
            file_size = int(size_output.strip())
        
        # 读取文件内容
        content = ssh_conn.download_file(file_path)
        if content is None:
            raise HTTPException(status_code=500, detail="下载失败")
        
        # 生成文件名
        safe_path = file_path.replace('/', '-').strip('-')
        filename = f"{host.host}_{safe_path}.log"
        
        # 3MB = 3 * 1024 * 1024 = 3145728 字节
        MAX_SIZE = 3 * 1024 * 1024
        
        if file_size > MAX_SIZE:
            # 文件大于3MB，压缩后下载
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr(filename, content)
            
            zip_buffer.seek(0)
            zip_filename = f"{host.host}_{safe_path}.zip"
            
            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
            )
        else:
            # 文件小于3MB，直接下载
            return {"content": content, "filename": filename}
            
    except Exception as e:
        print(f"下载文件错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# ==================== WebSocket路由 ====================
@app.websocket(CONTEXT_PATH + "/ws/logs/{host_id}")
async def websocket_logs(websocket: WebSocket, host_id: int):
    await websocket.accept()
    
    stream_manager.set_event_loop(asyncio.get_event_loop())
    
    stream_id = None
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            print(f"收到 WebSocket 消息: {message}")
            
            db = SessionLocal()
            try:
                host = db.query(SSHHost).filter(SSHHost.id == host_id).first()
                if not host:
                    await websocket.send_text(json.dumps({"error": "主机不存在"}))
                    continue
                
                ssh_conn = SSHManager.get_connection(host_id, {
                    'host': host.host,
                    'port': host.port,
                    'username': host.username,
                    'password': host.password,
                    'private_key': host.private_key
                })
                
                if not ssh_conn:
                    await websocket.send_text(json.dumps({"error": "SSH连接失败"}))
                    continue
                
                if message['type'] == 'file':
                    log_path = message['path']
                    lines = message.get('lines', 100)
                    stream_id = f"file_{host_id}_{log_path.replace('/', '_')}"
                    
                    print(f"开始跟踪文件日志: {log_path}, 行数: {lines}")
                    
                    test_cmd = f"test -f {log_path} && echo 'exists' || echo 'not exists'"
                    test_output, test_error = ssh_conn.execute_command(test_cmd)
                    print(f"文件检查结果: {test_output}")
                    
                    if 'not exists' in test_output:
                        await websocket.send_text(json.dumps({"error": f"文件不存在: {log_path}"}))
                        continue
                    
                    if not ssh_conn.is_text_file(log_path):
                        await websocket.send_text(json.dumps({
                            "error": f"文件 {log_path} 不是文本文件，无法查看。只支持查看文本格式的日志文件。"
                        }))
                        continue
                    
                    channel = ssh_conn.tail_log(log_path, lines, stream_id)
                    if channel:
                        stream_manager.add_stream(stream_id, ssh_conn, channel, 'file', message)
                        stream_manager.add_websocket(stream_id, websocket)
                        await websocket.send_text(json.dumps({
                            "type": "started",
                            "stream_id": stream_id,
                            "message": f"开始跟踪文件日志: {log_path}"
                        }))
                    else:
                        await websocket.send_text(json.dumps({"error": "无法创建日志流"}))
                
                elif message['type'] == 'docker':
                    container = message['container']
                    lines = message.get('lines', 100)
                    stream_id = f"docker_{host_id}_{container}"
                    
                    channel = ssh_conn.tail_docker_logs(container, lines, stream_id)
                    if channel:
                        stream_manager.add_stream(stream_id, ssh_conn, channel, 'docker', message)
                        stream_manager.add_websocket(stream_id, websocket)
                        await websocket.send_text(json.dumps({
                            "type": "started",
                            "stream_id": stream_id,
                            "message": "开始跟踪Docker日志"
                        }))
                    else:
                        await websocket.send_text(json.dumps({"error": "无法创建日志流"}))
                
                elif message['type'] == 'podman':
                    container = message['container']
                    lines = message.get('lines', 100)
                    stream_id = f"podman_{host_id}_{container}"
                    
                    channel = ssh_conn.tail_podman_logs(container, lines, stream_id)
                    if channel:
                        stream_manager.add_stream(stream_id, ssh_conn, channel, 'podman', message)
                        stream_manager.add_websocket(stream_id, websocket)
                        await websocket.send_text(json.dumps({
                            "type": "started",
                            "stream_id": stream_id,
                            "message": "开始跟踪Podman日志"
                        }))
                    else:
                        await websocket.send_text(json.dumps({"error": "无法创建日志流"}))
                
                elif message['type'] == 'k8s':
                    namespace = message.get('namespace', 'default')
                    pod = message['pod']
                    lines = message.get('lines', 100)
                    stream_id = f"k8s_{host_id}_{namespace}_{pod}"
                    
                    channel = ssh_conn.tail_k8s_logs(namespace, pod, lines, stream_id)
                    if channel:
                        stream_manager.add_stream(stream_id, ssh_conn, channel, 'k8s', message)
                        stream_manager.add_websocket(stream_id, websocket)
                        await websocket.send_text(json.dumps({
                            "type": "started",
                            "stream_id": stream_id,
                            "message": "开始跟踪K8s日志"
                        }))
                    else:
                        await websocket.send_text(json.dumps({"error": "无法创建日志流"}))
                
                elif message['type'] == 'stop':
                    if stream_id:
                        stream_manager.remove_stream(stream_id)
                        await websocket.send_text(json.dumps({
                            "type": "stopped",
                            "message": "停止跟踪日志"
                        }))
                
            finally:
                db.close()
    
    except WebSocketDisconnect:
        if stream_id:
            stream_manager.remove_websocket(stream_id, websocket)

# ==================== 日志历史 API ====================
@app.get(CONTEXT_PATH + "/api/hosts/{host_id}/log-history")
async def get_log_history(host_id: int):
    """获取主机的日志路径历史（只查未删除的）"""
    db = SessionLocal()
    try:
        histories = db.query(LogPathHistory).filter(
            LogPathHistory.host_id == host_id,
            LogPathHistory.is_deleted == False
        ).order_by(LogPathHistory.last_used.desc()).limit(20).all()
        
        return [
            {
                "id": h.id,
                "log_path": h.log_path,
                "last_used": h.last_used.isoformat() if h.last_used else None,
                "use_count": h.use_count
            }
            for h in histories
        ]
    except Exception as e:
        print(f"获取历史记录错误: {e}")
        return []
    finally:
        db.close()

@app.post(CONTEXT_PATH + "/api/hosts/{host_id}/log-history")
async def add_log_history(host_id: int, log_path: str):
    """添加或更新日志路径历史"""
    db = SessionLocal()
    try:
        existing = db.query(LogPathHistory).filter(
            LogPathHistory.host_id == host_id,
            LogPathHistory.log_path == log_path,
            LogPathHistory.is_deleted == False
        ).first()
        
        if existing:
            existing.use_count += 1
            existing.last_used = datetime.utcnow()
            db.commit()
        else:
            history = LogPathHistory(
                host_id=host_id,
                log_path=log_path,
                use_count=1,
                last_used=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            db.add(history)
            db.commit()
        
        return {"message": "历史记录已保存"}
    except Exception as e:
        print(f"保存历史记录错误: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post(CONTEXT_PATH + "/api/hosts/{host_id}/log-history/{history_id}/delete")
async def delete_log_history(host_id: int, history_id: int):
    """逻辑删除日志路径历史"""
    db = SessionLocal()
    try:
        history = db.query(LogPathHistory).filter(
            LogPathHistory.id == history_id,
            LogPathHistory.host_id == host_id,
            LogPathHistory.is_deleted == False
        ).first()
        
        if history:
            history.is_deleted = True
            history.deleted_at = datetime.utcnow()
            db.commit()
            return {"message": "删除成功"}
        else:
            raise HTTPException(status_code=404, detail="历史记录不存在")
    finally:
        db.close()

@app.post(CONTEXT_PATH + "/api/hosts/{host_id}/log-history/clear")
async def clear_log_history(host_id: int):
    """逻辑清空主机的日志路径历史"""
    db = SessionLocal()
    try:
        db.query(LogPathHistory).filter(
            LogPathHistory.host_id == host_id,
            LogPathHistory.is_deleted == False
        ).update({
            LogPathHistory.is_deleted: True,
            LogPathHistory.deleted_at: datetime.utcnow()
        })
        db.commit()
        return {"message": "历史记录已清空"}
    except Exception as e:
        print(f"清空历史记录错误: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get(CONTEXT_PATH + "/api/hosts/{host_id}/test-file")
async def test_file(host_id: int, file_path: str):
    """测试文件是否存在"""
    db = SessionLocal()
    try:
        host = db.query(SSHHost).filter(SSHHost.id == host_id).first()
        if not host:
            raise HTTPException(status_code=404, detail="主机不存在")
        
        ssh_conn = SSHManager.get_connection(host_id, {
            'host': host.host,
            'port': host.port,
            'username': host.username,
            'password': host.password,
            'private_key': host.private_key
        })
        
        if not ssh_conn:
            raise HTTPException(status_code=500, detail="SSH连接失败")
        
        command = f"test -f {file_path} && echo 'exists' || echo 'not exists'"
        output, error = ssh_conn.execute_command(command)
        
        return {"exists": "exists" in output, "path": file_path}
    finally:
        db.close()

# ==================== 静态文件服务（放在最后，避免拦截API路由） ====================
if STATIC_DIR and os.path.exists(STATIC_DIR):
    print(f"挂载静态文件目录: {STATIC_DIR}")
    
    # 挂载 assets 目录
    assets_dir = os.path.join(STATIC_DIR, 'assets')
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    
    # 根路径返回 index.html
    @app.get(CONTEXT_PATH + "/")
    async def root():
        index_path = os.path.join(STATIC_DIR, 'index.html')
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"error": "Index file not found"}
    
    # SPA 路由处理
    @app.get(CONTEXT_PATH + "/{full_path:path}")
    async def serve_spa(full_path: str):
        # 跳过 API 和 WebSocket 路由
        if full_path.startswith('api/') or full_path.startswith('ws/'):
            # 让其他路由处理
            raise HTTPException(status_code=404)
        
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # 返回 index.html 用于前端路由
        index_path = os.path.join(STATIC_DIR, 'index.html')
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"error": "Not found"}
else:
    print(f"警告: 静态文件目录不存在: {STATIC_DIR}")

# ==================== 启动入口 ====================
if __name__ == "__main__":
    print(f"启动 Ztailog 服务器...")
    print(f"访问地址: http://0.0.0.0:60501")
    uvicorn.run(app, host="0.0.0.0", port=60501)
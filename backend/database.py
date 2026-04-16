from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

db_path = os.path.join(BASE_DIR, 'ztailog.db')
engine = create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})

Base = declarative_base()

class SSHHost(Base):
    __tablename__ = 'ssh_hosts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, server_default="22")
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=True)
    private_key = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, server_default="0", nullable=False, index=True)

class LogConfig(Base):
    __tablename__ = 'log_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(Integer, nullable=False)
    log_type = Column(String(50), nullable=False)
    default_lines = Column(Integer, server_default="100")
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, server_default="0", nullable=False, index=True)

class LogPathHistory(Base):
    __tablename__ = 'log_path_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(Integer, nullable=False, index=True)
    log_path = Column(String(500), nullable=False)
    last_used = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), onupdate=datetime.utcnow)
    use_count = Column(Integer, server_default="1")
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, server_default="0", nullable=False, index=True)

def get_db_path():
    """获取数据库文件路径（支持打包后运行）"""
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    db_path = os.path.join(base_dir, 'ztailog.db')
    print(f"数据库路径: {db_path}")
    return db_path

# 数据库初始化
db_path = get_db_path()
engine = create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    """初始化数据库，创建所有表"""
    # 使用原始 sqlite3 模块
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建 ssh_hosts 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ssh_hosts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            host VARCHAR(255) NOT NULL,
            port INTEGER DEFAULT 22,
            username VARCHAR(100) NOT NULL,
            password VARCHAR(255),
            private_key TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            deleted_at DATETIME,
            is_deleted BOOLEAN DEFAULT 0 NOT NULL
        )
    """)
    
    # 创建 log_configs 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host_id INTEGER NOT NULL,
            log_type VARCHAR(50) NOT NULL,
            default_lines INTEGER DEFAULT 100,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            deleted_at DATETIME,
            is_deleted BOOLEAN DEFAULT 0 NOT NULL
        )
    """)
    
    # 创建 log_path_history 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_path_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host_id INTEGER NOT NULL,
            log_path VARCHAR(500) NOT NULL,
            last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
            use_count INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            deleted_at DATETIME,
            is_deleted BOOLEAN DEFAULT 0 NOT NULL
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_path_history_host_id ON log_path_history(host_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_path_history_is_deleted ON log_path_history(is_deleted)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_configs_is_deleted ON log_configs(is_deleted)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ssh_hosts_is_deleted ON ssh_hosts(is_deleted)")
    
    conn.commit()
    conn.close()
    
    print("数据库初始化完成")

if __name__ == "__main__":
    init_db()
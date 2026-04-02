from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
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
    port = Column(Integer, default=22)
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=True)
    private_key = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LogConfig(Base):
    __tablename__ = 'log_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(Integer, nullable=False)
    log_type = Column(String(50), nullable=False)  # file, docker, podman, k8s
    default_lines = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)

class LogPathHistory(Base):
    __tablename__ = 'log_path_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(Integer, nullable=False, index=True)
    log_path = Column(String(500), nullable=False)
    last_used = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    use_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

# 数据库初始化
db_path = os.path.join(os.path.dirname(__file__), 'ztailog.db')
engine = create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)
    print("数据库初始化完成")

# 如果直接运行此文件，初始化数据库
if __name__ == "__main__":
    init_db()
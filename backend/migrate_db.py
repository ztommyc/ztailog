#!/usr/bin/env python3
import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), 'ztailog.db')
    
    if not os.path.exists(db_path):
        print("数据库不存在，请先启动应用")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查并添加字段
    tables = ['ssh_hosts', 'log_configs', 'log_path_history']
    
    for table in tables:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN is_deleted INTEGER DEFAULT 0")
            print(f"已添加 {table}.is_deleted 字段")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e):
                print(f"{table}.is_deleted 字段已存在")
            else:
                print(f"添加 {table}.is_deleted 失败: {e}")
        
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN deleted_at TIMESTAMP")
            print(f"已添加 {table}.deleted_at 字段")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e):
                print(f"{table}.deleted_at 字段已存在")
            else:
                print(f"添加 {table}.deleted_at 失败: {e}")
        
        # 创建索引
        try:
            cursor.execute(f"CREATE INDEX idx_{table}_is_deleted ON {table}(is_deleted)")
            print(f"已创建 {table} 索引")
        except sqlite3.OperationalError as e:
            if 'already exists' in str(e):
                print(f"{table} 索引已存在")
    
    conn.commit()
    conn.close()
    print("数据库迁移完成")

if __name__ == "__main__":
    migrate()
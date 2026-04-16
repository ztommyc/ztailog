import sqlite3

def migrate_table_with_mapping(source_db, target_db, source_table_name,target_table_name, field_mapping):
    """
    从源数据库迁移一张表到目标数据库，支持字段映射
    
    :param source_db: 源数据库文件路径
    :param target_db: 目标数据库文件路径
    :param source_table_name: 要迁移的表名
    :param target_table_name: 要迁移的表名
    :param field_mapping: 字段映射字典，格式 {目标表字段: 源表字段}
                         例如 {'new_id': 'old_id', 'full_name': 'name'}
    """
    # 连接两个数据库
    src_conn = sqlite3.connect(source_db)
    tgt_conn = sqlite3.connect(target_db)
    
    src_cursor = src_conn.cursor()
    tgt_cursor = tgt_conn.cursor()
    
    try:
        # 1. 检查源表是否存在
        src_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (source_table_name,))
        if not src_cursor.fetchone():
            print(f"源数据库中的表 {source_table_name} 不存在")
            return
        
        # 2. 获取源表所有列名
        src_cursor.execute(f"PRAGMA table_info({source_table_name})")
        src_columns = [col[1] for col in src_cursor.fetchall()]
        print(f"源表列: {src_columns}")
        
        # 3. 获取目标表所有列名
        tgt_cursor.execute(f"PRAGMA table_info({target_table_name})")
        tgt_columns_info = tgt_cursor.fetchall()
        if not tgt_columns_info:
            print(f"目标数据库中的表 {target_table_name} 不存在")
            return
        tgt_columns = [col[1] for col in tgt_columns_info]
        print(f"目标表列: {tgt_columns}")
        
        # 4. 验证字段映射的有效性
        for tgt_field, src_field in field_mapping.items():
            if tgt_field not in tgt_columns:
                print(f"警告: 目标字段 {tgt_field} 在目标表中不存在，将被忽略")
            if src_field not in src_columns:
                print(f"警告: 源字段 {src_field} 在源表中不存在，将被忽略")
        
        # 5. 准备要插入的目标字段列表（只包含映射中有效的字段）
        insert_fields = []
        select_fields = []
        for tgt_field, src_field in field_mapping.items():
            if tgt_field in tgt_columns and src_field in src_columns:
                insert_fields.append(tgt_field)
                select_fields.append(src_field)
        
        if not insert_fields:
            print("没有有效的字段映射，无法迁移")
            return
        
        # 6. 构建SQL语句
        placeholders = ','.join(['?' for _ in insert_fields])
        insert_sql = f"INSERT INTO {target_table_name} ({','.join(insert_fields)}) VALUES ({placeholders})"
        select_sql = f"SELECT {','.join(select_fields)} FROM {source_table_name}"
        print(insert_sql) 
        print(select_sql) 
        # 7. 读取源表数据并插入目标表
        src_cursor.execute(select_sql)
        rows = src_cursor.fetchall()
        
        count = 0
        for row in rows:
            try:
                tgt_cursor.execute(insert_sql, row)
                count += 1
            except sqlite3.IntegrityError as e:
                print(f"插入失败（主键冲突等）: {e} - 数据: {row}")
            except Exception as e:
                print(f"插入失败: {e} - 数据: {row}")
        
        # 8. 提交事务
        tgt_conn.commit()
        print(f"成功迁移 {count} 行数据")
        
    except Exception as e:
        print(f"迁移过程中发生错误: {e}")
        tgt_conn.rollback()
    finally:
        src_conn.close()
        tgt_conn.close()


# ============= 使用示例 =============

if __name__ == "__main__":
    # 示例数据库文件路径
    source_db = "/home/deploy.db"
    target_db = "ztailog.db"
    source_table_name = "deploy_server"
    target_table_name = "ssh_hosts"
    # 字段映射：目标字段 -> 源字段
    field_mapping = {
        "id":"id", 
        "name":"server_name", 
        "host":"server_ip",
        "port":"ssh_port",
        "username":"server_user_name",
        "password":"server_password"
    }
    # 执行迁移
    migrate_table_with_mapping(source_db, target_db, source_table_name,target_table_name, field_mapping)

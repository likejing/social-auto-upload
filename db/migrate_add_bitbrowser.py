# -*- coding: utf-8 -*-
"""
数据库迁移脚本: 为已存在的 user_info 表添加比特浏览器相关字段
运行方式: python db/migrate_add_bitbrowser.py
"""
import sqlite3
import os

# 数据库文件路径
db_file = './database.db'

def migrate():
    """执行数据库迁移"""
    if not os.path.exists(db_file):
        print("数据库文件不存在，无需迁移")
        return

    # 连接到SQLite数据库
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    try:
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(user_info)")
        columns = [column[1] for column in cursor.fetchall()]

        # 添加 browser_type 字段
        if 'browser_type' not in columns:
            cursor.execute('''
                ALTER TABLE user_info ADD COLUMN browser_type TEXT DEFAULT 'playwright'
            ''')
            print("✅ 成功添加 browser_type 字段")
        else:
            print("ℹ️  browser_type 字段已存在，跳过")

        # 添加 bitbrowser_id 字段
        if 'bitbrowser_id' not in columns:
            cursor.execute('''
                ALTER TABLE user_info ADD COLUMN bitbrowser_id TEXT DEFAULT NULL
            ''')
            print("✅ 成功添加 bitbrowser_id 字段")
        else:
            print("ℹ️  bitbrowser_id 字段已存在，跳过")

        # 提交更改
        conn.commit()
        print("✅ 数据库迁移完成")

    except sqlite3.Error as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
    finally:
        # 关闭连接
        conn.close()


if __name__ == "__main__":
    migrate()

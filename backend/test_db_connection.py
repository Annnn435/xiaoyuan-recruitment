import os
import psycopg2

# 数据库连接信息
conn_info = {
    'dbname': 'recruitment_db',
    'user': 'recruitment_user',
    'password': 'jzj200366',
    'host': 'localhost',
    'port': '5432'
}

# 测试数据库连接
print("开始测试数据库连接...")
try:
    # 尝试连接数据库
    conn = psycopg2.connect(**conn_info)
    print("✅ 数据库连接成功!")
    
    # 创建游标对象
    cursor = conn.cursor()
    print("✅ 游标创建成功!")
    
    # 执行简单查询
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()[0]
    print(f"✅ 数据库版本: {db_version}")
    
    # 检查当前数据库名称
    cursor.execute("SELECT current_database();")
    current_db = cursor.fetchone()[0]
    print(f"✅ 当前连接的数据库: {current_db}")
    
    # 检查用户权限
    cursor.execute("SELECT * FROM information_schema.table_privileges WHERE grantee = current_user;")
    privileges = cursor.fetchall()
    print(f"✅ 查找到 {len(privileges)} 条权限记录")
    
    # 检查job表是否存在（如果之前创建过）
    cursor.execute(""" 
        SELECT EXISTS (
            SELECT FROM pg_tables 
            WHERE schemaname = 'public' AND tablename = 'job'
        );
    """)
    job_table_exists = cursor.fetchone()[0]
    print(f"✅ job表是否存在: {job_table_exists}")
    
    # 如果job表存在，检查记录数
    if job_table_exists:
        cursor.execute("SELECT COUNT(*) FROM job;")
        job_count = cursor.fetchone()[0]
        print(f"✅ job表中的记录数: {job_count}")
    
    # 关闭连接
    cursor.close()
    conn.close()
    print("✅ 数据库连接已关闭")
    
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
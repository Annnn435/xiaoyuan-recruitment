import os
import psycopg2

# PostgreSQL管理员连接信息
# 注意：请根据您的PostgreSQL管理员账号信息修改以下内容
admin_conn_info = {
    'dbname': 'postgres',  # 使用postgres数据库连接
    'user': 'postgres',    # 管理员用户名，通常是postgres
    'password': 'jzj200366',    # 管理员密码，请根据实际情况修改
    'host': 'localhost',
    'port': '5432'
}

print("开始修复权限并初始化数据库...")
try:
    # 使用管理员权限连接
    admin_conn = psycopg2.connect(**admin_conn_info)
    admin_conn.autocommit = True
    admin_cursor = admin_conn.cursor()
    print("✅ 成功以管理员身份连接数据库")
    
    # 检查recruitment_user是否存在
    admin_cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = 'recruitment_user';")
    user_exists = admin_cursor.fetchone() is not None
    
    if not user_exists:
        # 创建用户
        print("⚠️ 用户recruitment_user不存在，创建新用户...")
        admin_cursor.execute("CREATE USER recruitment_user WITH PASSWORD 'jzj200366';")
    else:
        print("✅ 用户recruitment_user已存在")
    
    # 检查recruitment_db是否存在
    admin_cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'recruitment_db';")
    db_exists = admin_cursor.fetchone() is not None
    
    if not db_exists:
        # 创建数据库
        print("⚠️ 数据库recruitment_db不存在，创建新数据库...")
        admin_cursor.execute("CREATE DATABASE recruitment_db OWNER recruitment_user;")
    else:
        print("✅ 数据库recruitment_db已存在")
    
    # 授予用户对数据库的权限
    print("正在授予用户对数据库的权限...")
    admin_cursor.execute("GRANT ALL PRIVILEGES ON DATABASE recruitment_db TO recruitment_user;")
    print("✅ 成功授予数据库权限")
    
    # 关闭管理员连接
    admin_cursor.close()
    admin_conn.close()
    print("✅ 管理员连接已关闭")
    
    # 现在使用recruitment_user连接recruitment_db并创建表
    user_conn_info = {
        'dbname': 'recruitment_db',
        'user': 'recruitment_user',
        'password': 'jzj200366',
        'host': 'localhost',
        'port': '5432'
    }
    
    user_conn = psycopg2.connect(**user_conn_info)
    user_conn.autocommit = True
    user_cursor = user_conn.cursor()
    print("✅ 成功以普通用户身份连接数据库")
    
    # 授予模式权限
    user_cursor.execute("GRANT ALL PRIVILEGES ON SCHEMA public TO recruitment_user;")
    print("✅ 成功授予模式权限")
    
    # 创建job表
    print("正在创建job表...")
    user_cursor.execute("""
        CREATE TABLE IF NOT EXISTS job (
            id SERIAL PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            company VARCHAR(100) NOT NULL,
            location VARCHAR(100),
            salary_min INTEGER,
            salary_max INTEGER,
            description TEXT,
            posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("✅ job表创建成功")
    
    # 插入示例数据
    print("正在插入示例数据...")
    user_cursor.execute("""
        INSERT INTO job (title, company, location, salary_min, salary_max, description)
        VALUES
            ('高级Python开发工程师', '科技创新有限公司', '北京', 25000, 40000, '负责后端系统开发和优化'),
            ('前端开发工程师', '互联网科技公司', '上海', 20000, 35000, '负责Web前端开发和用户界面优化')
        ON CONFLICT DO NOTHING;
    """)
    print("✅ 示例数据插入成功")
    
    # 验证表创建和数据插入
    user_cursor.execute("SELECT COUNT(*) FROM job;")
    count = user_cursor.fetchone()[0]
    print(f"✅ job表中当前有 {count} 条记录")
    
    # 关闭用户连接
    user_cursor.close()
    user_conn.close()
    print("✅ 用户连接已关闭")
    print("✅ 权限修复和数据库初始化完成！")
    
except Exception as e:
    print(f"❌ 发生错误: {e}")
    print("请检查PostgreSQL管理员用户名和密码是否正确")
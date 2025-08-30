import os
import psycopg2

# PostgreSQL管理员连接信息
admin_conn_info = {
    'dbname': 'recruitment_db',  # 直接连接到目标数据库
    'user': 'postgres',          # 管理员用户名
    'password': 'jzj200366',     # 管理员密码
    'host': 'localhost',
    'port': '5432'
}

print("开始使用管理员账号初始化数据库...")
try:
    # 使用管理员权限直接连接到recruitment_db
    conn = psycopg2.connect(**admin_conn_info)
    conn.autocommit = True
    cursor = conn.cursor()
    print("✅ 成功以管理员身份连接到recruitment_db数据库")
    
    # 创建job表（如果不存在）
    print("正在创建job表...")
    cursor.execute("""
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
    
    # 授予普通用户对job表的所有权限
    print("正在授予recruitment_user对job表的权限...")
    cursor.execute("GRANT ALL PRIVILEGES ON TABLE job TO recruitment_user;")
    cursor.execute("GRANT USAGE, SELECT ON SEQUENCE job_id_seq TO recruitment_user;")  # 授予序列权限
    print("✅ 权限授予成功")
    
    # 清空表（如果需要重新插入数据）
    print("正在清空job表...")
    cursor.execute("TRUNCATE TABLE job RESTART IDENTITY;")
    print("✅ job表已清空")
    
    # 插入示例数据
    print("正在插入示例数据...")
    cursor.execute("""
        INSERT INTO job (title, company, location, salary_min, salary_max, description)
        VALUES
            ('高级Python开发工程师', '科技创新有限公司', '北京', 25000, 40000, '负责后端系统开发和优化'),
            ('前端开发工程师', '互联网科技公司', '上海', 20000, 35000, '负责Web前端开发和用户界面优化'),
            ('数据分析师', '金融科技公司', '深圳', 18000, 30000, '负责数据分析和可视化'),
            ('产品经理', '电子商务公司', '杭州', 22000, 38000, '负责产品规划和管理')
    """)
    print("✅ 示例数据插入成功")
    
    # 验证数据插入
    cursor.execute("SELECT COUNT(*) FROM job;")
    count = cursor.fetchone()[0]
    print(f"✅ job表中当前有 {count} 条记录")
    
    # 关闭连接
    cursor.close()
    conn.close()
    print("✅ 数据库连接已关闭")
    print("✅ 数据库初始化完成！")
    
except Exception as e:
    print(f"❌ 发生错误: {e}")
    print("请检查PostgreSQL管理员用户名和密码是否正确")
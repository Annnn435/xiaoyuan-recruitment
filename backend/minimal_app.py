import os
from flask import Flask, jsonify
import psycopg2
from datetime import datetime

app = Flask(__name__)

# 数据库连接配置
DB_CONFIG = {
    'dbname': 'recruitment_db',
    'user': 'postgres',  # 直接使用管理员账号
    'password': 'jzj200366',  # 管理员密码
    'host': 'localhost',
    'port': '5432'
}

# 初始化数据库函数
# 注意：不再使用before_first_request装饰器，而是在main函数中直接调用
def init_database():
    print("初始化数据库...")
    try:
        # 连接数据库
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 先删除旧表（如果存在），确保表结构是最新的
        cursor.execute("DROP TABLE IF EXISTS job;")
        print("✅ 已删除旧的job表")
        
        # 创建新的job表（包含所有必要字段）
        cursor.execute("""
            CREATE TABLE job (
                id SERIAL PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                company VARCHAR(100) NOT NULL,
                location VARCHAR(100),
                salary_min INTEGER,
                salary_max INTEGER,
                description TEXT,
                job_type VARCHAR(50),
                experience VARCHAR(50),
                education VARCHAR(50),
                industry VARCHAR(100),
                tags TEXT[],
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deadline DATE
            );
        """)
        print("✅ 新的job表已创建")
        
        # 插入10条示例数据
        sample_jobs = [
            ('高级Python开发工程师', '科技创新有限公司', '北京', 25000, 40000, '负责后端系统开发和优化', '全职', '3-5年', '本科及以上', '互联网', '{Python,Flask,PostgreSQL}', '2025-03-31'),
            ('前端开发工程师', '互联网科技公司', '上海', 20000, 35000, '负责Web前端开发和用户界面优化', '全职', '1-3年', '本科及以上', '互联网', '{React,TypeScript,Ant Design}', '2025-03-20'),
            ('数据分析师', '金融科技公司', '杭州', 18000, 30000, '负责数据分析和数据可视化工作', '全职', '2-5年', '本科及以上', '金融', '{Python,SQL,数据分析}', '2025-04-15'),
            ('产品经理', '电商平台', '广州', 22000, 38000, '负责产品规划和用户需求分析', '全职', '3-5年', '本科及以上', '电商', '{产品设计,用户研究}', '2025-03-10'),
            ('UI设计师', '游戏开发公司', '成都', 15000, 28000, '负责游戏界面设计和用户体验优化', '全职', '1-3年', '本科及以上', '游戏', '{UI设计,用户体验}', '2025-03-25'),
            ('测试工程师', '软件外包公司', '武汉', 12000, 22000, '负责软件测试和质量保证工作', '全职', '1-3年', '本科及以上', '软件服务', '{自动化测试,性能测试}', '2025-03-18'),
            ('运维工程师', '云计算公司', '深圳', 18000, 32000, '负责云服务的运维和管理工作', '全职', '2-5年', '本科及以上', '云计算', '{Linux,Docker,Kubernetes}', '2025-04-05'),
            ('人力资源专员', '咨询公司', '南京', 8000, 15000, '负责人事招聘和员工关系管理', '全职', '1-3年', '本科及以上', '咨询', '{招聘,HR}', '2025-03-12'),
            ('财务分析师', '跨国企业', '上海', 15000, 28000, '负责财务分析和报表编制工作', '全职', '2-4年', '本科及以上', '制造业', '{财务分析,报表}', '2025-03-28'),
            ('销售经理', '医疗器械公司', '全国', 20000, 50000, '负责销售团队管理和销售目标达成', '全职', '3-6年', '本科及以上', '医疗健康', '{销售管理,团队管理}', '2025-04-10')
        ]
        
        # 插入示例数据
        for job in sample_jobs:
            cursor.execute(
                "INSERT INTO job (title, company, location, salary_min, salary_max, description, job_type, experience, education, industry, tags, deadline) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                job
            )
        print("✅ 已成功插入10条示例数据")
        
        # 关闭连接
        cursor.close()
        conn.close()
        print("✅ 数据库初始化完成")
        
    except Exception as e:
        print(f"❌ 数据库初始化错误: {str(e)}")

# 健康检查接口
@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy'})

# 职位列表接口
@app.route('/api/jobs')
def get_jobs():
    try:
        # 直接使用psycopg2查询
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, company, location, salary_min, salary_max, job_type, experience, education, industry, posted_at, deadline FROM job LIMIT 100;")
        jobs = cursor.fetchall()
        
        # 格式化结果
        result = []
        for job in jobs:
            result.append({
                'id': job[0],
                'title': job[1],
                'company': job[2],
                'location': job[3],
                'salary_min': job[4],
                'salary_max': job[5],
                'job_type': job[6],
                'experience': job[7],
                'education': job[8],
                'industry': job[9],
                'posted_at': job[10].strftime('%Y-%m-%d'),
                'deadline': job[11].strftime('%Y-%m-%d')
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'jobs': result, 'total': len(result)})
        
    except Exception as e:
        print(f"❌ 查询错误: {str(e)}")
        return jsonify({'error': str(e), 'message': '查询失败'}), 500

if __name__ == '__main__':
    print("启动最小化应用...")
    # 在应用启动前直接调用初始化数据库函数
    init_database()
    app.run(debug=True)
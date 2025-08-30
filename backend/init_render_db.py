import os
from simple_app import app, db, Job
from datetime import datetime

def init_render_database():
    """专门用于Render部署的数据库初始化"""
    with app.app_context():
        try:
            print("🔄 Render环境 - 开始初始化数据库...")
            
            # 删除所有表（如果存在）
            db.drop_all()
            print("🗑️ 已清理旧表")
            
            # 创建所有表
            db.create_all()
            print("✅ 数据库表创建成功")
            
            # 插入示例数据
            sample_jobs = [
                Job(
                    title='高级Python开发工程师',
                    company='科技创新有限公司',
                    location='北京',
                    salary_min=25000,
                    salary_max=40000,
                    description='负责后端系统开发和优化，参与架构设计，解决技术难题',
                    source='智联招聘',
                    status='招聘中',
                    target_group='社招',
                    job_nature='全职',
                    experience='3-5年',
                    education='本科',
                    industry='互联网'
                ),
                Job(
                    title='前端开发工程师',
                    company='互联网科技公司',
                    location='上海',
                    salary_min=20000,
                    salary_max=35000,
                    description='负责Web前端开发和用户界面优化',
                    source='51job',
                    status='招聘中',
                    target_group='校招',
                    job_nature='全职',
                    experience='1-3年',
                    education='本科',
                    industry='互联网'
                )
            ]
            
            db.session.add_all(sample_jobs)
            db.session.commit()
            print(f"✅ 已插入 {len(sample_jobs)} 条示例数据")
            
            # 验证数据
            job_count = Job.query.count()
            print(f"📊 数据库中共有 {job_count} 条记录")
            
        except Exception as e:
            print(f"❌ 数据库初始化错误: {str(e)}")
            raise e

if __name__ == '__main__':
    init_render_database()
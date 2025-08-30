import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

# 创建Flask应用
app = Flask(__name__)

# 配置应用
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key'

# 修改这一行，使用环境变量配置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'postgresql://postgres:jzj200366@localhost:5432/recruitment_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化扩展
db = SQLAlchemy(app)
# 配置CORS，允许所有来源的请求
cors = CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]}})

# 添加CORS预检请求处理
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# 定义Job模型
class Job(db.Model):
    __tablename__ = 'job'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    description = db.Column(db.Text)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(50))  # 招聘来源，如51job、智联等
    url = db.Column(db.String(255))    # 原始招聘链接
    status = db.Column(db.String(20))  # 职位状态
    target_group = db.Column(db.String(50))  # 目标人群
    job_nature = db.Column(db.String(50))  # 工作性质
    experience = db.Column(db.String(50))  # 经验要求
    education = db.Column(db.String(50))  # 学历要求
    industry = db.Column(db.String(100))  # 所属行业

# 添加健康检查路由
@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy'})

# 添加职位列表路由
@app.route('/api/jobs')
def get_jobs():
    from flask import request
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '')
        source = request.args.get('source', '')
        location = request.args.get('location', '')
        target_group = request.args.get('target_group', '')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 构建查询
        query = Job.query
        
        # 应用筛选条件
        if keyword:
            query = query.filter(
                db.or_(
                    Job.title.ilike(f'%{keyword}%'),
                    Job.company.ilike(f'%{keyword}%'),
                    Job.description.ilike(f'%{keyword}%')
                )
            )
        if source:
            query = query.filter(Job.source == source)
        if location:
            query = query.filter(Job.location.ilike(f'%{location}%'))
        if target_group:
            query = query.filter(Job.target_group == target_group)
        
        # 计算总数
        total = query.count()
        
        # 分页
        jobs = query.order_by(Job.posted_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        # 格式化结果
        result = [{
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'salary_min': job.salary_min,
            'salary_max': job.salary_max,
            'description': job.description,
            'posted_at': job.posted_at.strftime('%Y-%m-%d %H:%M:%S') if job.posted_at else None,
            'source': job.source,
            'url': job.url,
            'status': job.status,
            'target_group': job.target_group,
            'job_nature': job.job_nature,
            'experience': job.experience,
            'education': job.education,
            'industry': job.industry
        } for job in jobs]
        
        return jsonify({
            'jobs': result, 
            'total': total,
            'page': page,
            'page_size': page_size,
            'pages': (total + page_size - 1) // page_size
        })
    except Exception as e:
        print(f"查询错误: {str(e)}")
        return jsonify({'error': str(e), 'message': '查询职位列表失败'}), 500

# 在文件最后修改这部分
if __name__ == '__main__':
    # 在启动前初始化数据库
    with app.app_context():
        try:
            print("🔄 开始初始化数据库...")
            db.create_all()
            print("✅ 数据库表创建成功")
            
            # 检查是否已有数据
            job_count = Job.query.count()
            if job_count == 0:
                print("📝 插入示例数据...")
                sample_jobs = [
                    Job(
                        title='高级Python开发工程师',
                        company='科技创新有限公司',
                        location='北京',
                        salary_min=25000,
                        salary_max=40000,
                        description='负责后端系统开发和优化，参与架构设计，解决技术难题',
                        source='智联招聘',
                        url='https://example.com/job1',
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
                        description='负责Web前端开发和用户界面优化，使用React技术栈',
                        source='51job',
                        url='https://example.com/job2',
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
            else:
                print(f"ℹ️ 数据库中已有 {job_count} 条记录")
                
        except Exception as e:
            print(f"❌ 数据库初始化错误: {str(e)}")
            # 不要因为数据库错误而停止应用启动
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 启动应用，端口: {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # 当作为模块导入时也初始化数据库
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"模块导入时数据库初始化错误: {str(e)}")
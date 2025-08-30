from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from flask_caching import cache
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload
from .. import db
from ..models.job import Job
from ..schemas.job_schema import JobSchema, JobFilterSchema
from ..utils.decorators import rate_limit, log_request
from ..utils.pagination import paginate_results
from datetime import datetime, timezone
from .. import db, cache, limiter  # 从app包中导入已初始化的实例

# 初始化蓝图
job_bp = Blueprint('job', __name__)

# 初始化序列化器
job_schema = JobSchema()
jobs_schema = JobSchema(many=True)
filter_schema = JobFilterSchema()

@job_bp.route('', methods=['GET'])
@log_request  # 企业级请求日志记录
@rate_limit(limit="100 per minute")  # 接口限流
@cache.cached(timeout=60, query_string=True)  # 缓存查询结果，1分钟
def get_jobs():
    """获取职位列表，支持复杂筛选和分页（企业级查询接口）"""
    # 验证查询参数
    errors = filter_schema.validate(request.args)
    if errors:
        return jsonify({'error': 'Validation error', 'details': errors}), 400
    
    # 解析筛选参数
    params = filter_schema.load(request.args)
    
    # 构建查询（企业级查询优化）
    query = Job.query
    
    # 基本筛选条件
    if params.get('company_name'):
        query = query.filter(Job.company_name.ilike(f"%{params['company_name']}%"))
    
    if params.get('company_type'):
        query = query.filter(Job.company_type == params['company_type'])
    
    if params.get('location'):
        query = query.filter(Job.location.ilike(f"%{params['location']}%"))
    
    if params.get('recruitment_type'):
        query = query.filter(Job.recruitment_type == params['recruitment_type'])
    
    if params.get('target_group'):
        query = query.filter(Job.target_group == params['target_group'])
    
    if params.get('job_name'):
        query = query.filter(Job.job_name.ilike(f"%{params['job_name']}%"))
    
    if params.get('delivery_status'):
        query = query.filter(Job.delivery_status == params['delivery_status'])
    
    # 日期范围筛选
    if params.get('start_date'):
        start_date = datetime.fromisoformat(params['start_date']).replace(tzinfo=timezone.utc)
        query = query.filter(Job.updated_at >= start_date)
    
    if params.get('end_date'):
        end_date = datetime.fromisoformat(params['end_date']).replace(tzinfo=timezone.utc)
        query = query.filter(Job.updated_at <= end_date)
    
    # 高级搜索（全文搜索）
    if params.get('keyword'):
        keyword = params['keyword']
        query = query.filter(
            or_(
                Job.company_name.ilike(f"%{keyword}%"),
                Job.job_name.ilike(f"%{keyword}%"),
                Job.description.ilike(f"%{keyword}%"),
                Job.requirements.ilike(f"%{keyword}%")
            )
        )
    
    # 排序
    sort_by = params.get('sort_by', 'updated_at')
    sort_order = params.get('sort_order', 'desc')
    
    if sort_order == 'desc':
        query = query.order_by(getattr(Job, sort_by).desc())
    else:
        query = query.order_by(getattr(Job, sort_by).asc())
    
    # 分页处理
    page = params.get('page', 1)
    page_size = params.get('page_size', 10)
    
    # 执行分页查询
    paginated = paginate_results(query, page, page_size)
    
    return jsonify({
        'data': jobs_schema.dump(paginated.items),
        'pagination': {
            'total': paginated.total,
            'page': page,
            'page_size': page_size,
            'pages': paginated.pages
        }
    })

@job_bp.route('/<int:job_id>', methods=['GET'])
@log_request
@rate_limit(limit="200 per minute")
@cache.cached(timeout=300, query_string=True)  # 缓存更久，5分钟
def get_job_detail(job_id):
    """获取职位详情"""
    job = Job.query.get_or_404(job_id)
    return jsonify(job_schema.dump(job))

@job_bp.route('/<int:job_id>/delivery-status', methods=['PATCH'])
@jwt_required()  # 企业级身份验证
@log_request
@rate_limit(limit="50 per minute")
def update_delivery_status(job_id):
    """更新投递状态（需要认证）"""
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Missing status parameter'}), 400
    
    valid_statuses = ['未投递', '已投递', '已笔试', '已面试', '已挂', '面试通过', '暂不投递']
    if data['status'] not in valid_statuses:
        return jsonify({'error': f'Status must be one of: {", ".join(valid_statuses)}'}), 400
    
    job = Job.query.get_or_404(job_id)
    job.delivery_status = data['status']
    job.updated_at = datetime.now(timezone.utc)
    
    db.session.commit()
    
    # 清除相关缓存
    cache.clear()
    
    return jsonify({
        'message': 'Delivery status updated successfully',
        'job_id': job_id,
        'status': data['status']
    })

@job_bp.route('/<int:job_id>/deliver', methods=['POST'])
@jwt_required()
@log_request
@rate_limit(limit="30 per minute")
def deliver_job(job_id):
    """投递职位（需要认证）"""
    job = Job.query.get_or_404(job_id)
    
    # 检查是否已截止
    if job.deadline and job.deadline < datetime.now(timezone.utc):
        return jsonify({'error': 'This job has expired'}), 400
    
    # 检查是否已投递
    if job.delivery_status == '已投递':
        return jsonify({'error': 'You have already delivered this job'}), 400
    
    # 更新状态
    job.delivery_status = '已投递'
    job.updated_at = datetime.now(timezone.utc)
    
    # 记录投递历史（企业级数据追踪）
    from ..models.delivery import Delivery
    new_delivery = Delivery(
        user_id=current_user.id,
        job_id=job_id,
        delivery_time=datetime.now(timezone.utc)
    )
    db.session.add(new_delivery)
    db.session.commit()
    
    # 清除缓存
    cache.clear()
    
    return jsonify({
        'message': 'Job delivered successfully',
        'job_id': job_id,
        'delivery_time': new_delivery.delivery_time.isoformat()
    })


@job_bp.route('/api/jobs', methods=['GET'])
def get_jobs():
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 构建查询
        query = Job.query
        
        # 分页查询
        pagination = query.order_by(Job.posted_at.desc()).paginate(page=page, per_page=per_page)
        jobs = pagination.items
        
        # 格式化结果
        result = {
            'jobs': [{
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'posted_at': job.posted_at.isoformat() if job.posted_at else None
            } for job in jobs],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

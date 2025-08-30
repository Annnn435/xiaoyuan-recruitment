from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
from datetime import datetime

# 示例数据，替代数据库
SAMPLE_JOBS = [
    {
        'id': 1,
        'title': '高级Python开发工程师',
        'company': '科技创新有限公司',
        'location': '北京',
        'salary_min': 25000,
        'salary_max': 40000,
        'description': '负责后端系统开发和优化，参与架构设计，解决技术难题',
        'posted_at': '2025-08-30 10:00:00',
        'source': '智联招聘',
        'url': 'https://example.com/job1',
        'status': '招聘中',
        'target_group': '社招',
        'job_nature': '全职',
        'experience': '3-5年',
        'education': '本科',
        'industry': '互联网'
    },
    {
        'id': 2,
        'title': '前端开发工程师',
        'company': '互联网科技公司',
        'location': '上海',
        'salary_min': 20000,
        'salary_max': 35000,
        'description': '负责Web前端开发和用户界面优化，使用React技术栈',
        'posted_at': '2025-08-30 09:30:00',
        'source': '51job',
        'url': 'https://example.com/job2',
        'status': '招聘中',
        'target_group': '校招',
        'job_nature': '全职',
        'experience': '1-3年',
        'education': '本科',
        'industry': '互联网'
    },
    {
        'id': 3,
        'title': '数据分析师',
        'company': '数据科技有限公司',
        'location': '深圳',
        'salary_min': 18000,
        'salary_max': 30000,
        'description': '负责数据挖掘和分析，制作数据报告，支持业务决策',
        'posted_at': '2025-08-30 08:45:00',
        'source': '智联招聘',
        'url': 'https://example.com/job3',
        'status': '招聘中',
        'target_group': '社招',
        'job_nature': '全职',
        'experience': '2-4年',
        'education': '本科',
        'industry': '数据服务'
    },
    {
        'id': 4,
        'title': 'UI/UX设计师',
        'company': '设计工作室',
        'location': '杭州',
        'salary_min': 15000,
        'salary_max': 25000,
        'description': '负责产品界面设计和用户体验优化，参与产品原型设计',
        'posted_at': '2025-08-30 07:20:00',
        'source': '51job',
        'url': 'https://example.com/job4',
        'status': '招聘中',
        'target_group': '校招',
        'job_nature': '全职',
        'experience': '1-2年',
        'education': '专科',
        'industry': '设计'
    }
]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 设置CORS头
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.end_headers()
        
        try:
            # 解析查询参数
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # 获取参数
            keyword = query_params.get('keyword', [''])[0]
            source = query_params.get('source', [''])[0]
            location = query_params.get('location', [''])[0]
            target_group = query_params.get('target_group', [''])[0]
            page = int(query_params.get('page', ['1'])[0])
            page_size = int(query_params.get('page_size', ['20'])[0])
            sort_field = query_params.get('sort_field', ['posted_at'])[0]
            sort_order = query_params.get('sort_order', ['descend'])[0]
            
            # 筛选数据
            filtered_jobs = SAMPLE_JOBS.copy()
            
            if keyword:
                filtered_jobs = [
                    job for job in filtered_jobs
                    if keyword.lower() in job['title'].lower() or 
                       keyword.lower() in job['company'].lower() or 
                       keyword.lower() in job['description'].lower()
                ]
            
            if source:
                filtered_jobs = [job for job in filtered_jobs if job['source'] == source]
            
            if location:
                filtered_jobs = [job for job in filtered_jobs if location.lower() in job['location'].lower()]
            
            if target_group:
                filtered_jobs = [job for job in filtered_jobs if job['target_group'] == target_group]
            
            # 排序
            reverse = sort_order == 'descend'
            if sort_field == 'posted_at':
                filtered_jobs.sort(key=lambda x: x['posted_at'], reverse=reverse)
            elif sort_field == 'salary_min':
                filtered_jobs.sort(key=lambda x: x['salary_min'] or 0, reverse=reverse)
            elif sort_field == 'salary_max':
                filtered_jobs.sort(key=lambda x: x['salary_max'] or 0, reverse=reverse)
            
            # 分页
            total = len(filtered_jobs)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_jobs = filtered_jobs[start_idx:end_idx]
            
            # 构建响应
            response = {
                'jobs': paginated_jobs,
                'total': total,
                'page': page,
                'page_size': page_size,
                'pages': (total + page_size - 1) // page_size
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            error_response = {
                'error': str(e),
                'message': '查询职位列表失败'
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
    
    def do_OPTIONS(self):
        # 处理预检请求
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.end_headers()
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from prometheus_flask_exporter import PrometheusMetrics
from sqlalchemy.dialects.postgresql import JSONB  # 添加JSONB导入

# 创建扩展实例
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cache = Cache()
limiter = Limiter(key_func=get_remote_address)

# 函数用于创建应用
def create_app(config_name=None):
    app = Flask(__name__)
    
    # 从环境变量或配置文件加载配置
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'dev')
    
    # 导入配置
    from .config import config_by_name
    app.config.from_object(config_by_name[config_name])
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)
    cache.init_app(app)
    limiter.init_app(app)
    
    # 初始化Prometheus指标
    metrics = PrometheusMetrics(app)
    
    # 导入并注册蓝图
    from .routes.job_routes import job_bp
    app.register_blueprint(job_bp)
    
    # 导入其他必要的路由
    # from .routes.user_routes import user_bp
    # app.register_blueprint(user_bp)
    
    # 注册全局错误处理器
    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad request'}, 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return {'error': 'Unauthorized'}, 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return {'error': 'Forbidden'}, 403
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return {'error': 'Internal server error'}, 500
    
    # 添加健康检查端点
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy'}
    
    # 记录应用启动信息
    app.logger.info(f"Application started in {config_name} mode")
    
    return app

# 确保在模块级别也有db实例，以便flask db命令能够访问它

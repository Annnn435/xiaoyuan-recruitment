import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.dialects.postgresql import JSONB  # 正确导入JSONB类型
import sys

# 添加backend目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 创建一个最小的Flask应用实例
app = Flask(__name__)

# 配置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'postgresql://username:password@localhost:5432/jobsdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库和迁移
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 定义一个简单的模型（仅用于初始化迁移）
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    description = db.Column(db.Text)
    posted_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    tags = db.Column(JSONB)  # 使用正确导入的JSONB类型

if __name__ == '__main__':
    with app.app_context():
        print("数据库初始化脚本已启动")
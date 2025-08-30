from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import Index, Text
from sqlalchemy.dialects.postgresql import JSONB
from .. import db

class Job(db.Model):
    """企业级职位信息模型，基于PostgreSQL"""
    __tablename__ = 'jobs'
    
    id = db.Column(db.BigInteger, primary_key=True)
    company_name = db.Column(db.String(255), nullable=False, index=True)
    company_type = db.Column(db.String(100), index=True)
    industry = db.Column(db.String(100), index=True)
    recruitment_type = db.Column(db.String(100), index=True)
    location = db.Column(db.String(255), index=True)
    target_group = db.Column(db.String(100), index=True)
    job_name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(Text)  # 详细岗位描述
    requirements = db.Column(Text)  # 岗位要求
    deadline = db.Column(db.DateTime(timezone=True))  # 带时区的时间
    url = db.Column(db.String(512))
    announcement = db.Column(Text)  # 招聘公告
    referral_code = db.Column(db.String(100))
    source = db.Column(db.String(100), index=True)  # 数据来源网站
    source_id = db.Column(db.String(100))  # 来源网站的ID，用于去重
    delivery_status = db.Column(db.String(50), default='未投递', index=True)
    metadata_info = db.Column(JSONB)  # PostgreSQL特有的JSONB类型，存储额外元数据
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # 企业级索引设计，优化查询性能
    __table_args__ = (
        Index('idx_company_job', 'company_name', 'job_name'),  # 联合索引
        Index('idx_deadline', 'deadline'),
        Index('idx_updated_at', 'updated_at'),
        Index('idx_source_source_id', 'source', 'source_id', unique=True),  # 唯一索引，防止重复抓取
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于API响应"""
        return {
            'id': self.id,
            'companyName': self.company_name,
            'companyType': self.company_type,
            'industry': self.industry,
            'recruitmentType': self.recruitment_type,
            'location': self.location,
            'targetGroup': self.target_group,
            'jobName': self.job_name,
            'description': self.description,
            'requirements': self.requirements,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'url': self.url,
            'announcement': self.announcement,
            'referralCode': self.referral_code,
            'source': self.source,
            'deliveryStatus': self.delivery_status,
            'metadata': self.metadata_info,
            'createdAt': self.created_at.isoformat(),
            'updateTime': self.updated_at.isoformat()
        }
    
    @classmethod
    def create_or_update(cls, job_data: Dict[str, Any]) -> 'Job':
        """创建或更新职位信息（企业级数据同步策略）"""
        # 先尝试通过source和source_id查找现有记录
        existing_job = cls.query.filter(
            cls.source == job_data.get('source'),
            cls.source_id == job_data.get('source_id')
        ).first()
        
        if existing_job:
            # 更新现有记录
            for key, value in job_data.items():
                if hasattr(existing_job, key) and key != 'id':
                    setattr(existing_job, key, value)
            return existing_job
        else:
            # 创建新记录
            new_job = cls(**job_data)
            db.session.add(new_job)
            return new_job

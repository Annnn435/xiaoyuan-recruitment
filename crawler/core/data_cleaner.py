import re
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger('data_cleaner')

class DataCleaner:
    """数据清洗器 - 标准化和清洗爬取的数据"""
    
    def __init__(self):
        # 薪资范围正则表达式
        self.salary_patterns = [
            r'(\d+)[kK][-~](\d+)[kK]',  # 10k-20k
            r'(\d+)[-~](\d+)[万千]',     # 1-2万
            r'(\d+)[万千][-~](\d+)[万千]', # 1万-2万
            r'(\d+)[-~](\d+)',          # 10000-20000
        ]
        
        # 学历映射
        self.education_mapping = {
            '不限': '不限',
            '中专': '中专',
            '高中': '高中', 
            '大专': '大专',
            '本科': '本科',
            '硕士': '硕士',
            '博士': '博士',
            'MBA': '硕士',
            '学士': '本科'
        }
        
        # 经验映射
        self.experience_mapping = {
            '不限': '不限',
            '应届': '应届生',
            '应届生': '应届生',
            '1年以下': '1年以下',
            '1-3年': '1-3年',
            '3-5年': '3-5年',
            '5-10年': '5-10年',
            '10年以上': '10年以上'
        }
    
    def clean_job_data(self, job_data: Dict) -> Dict:
        """清洗单个职位数据"""
        cleaned_data = job_data.copy()
        
        # 清洗职位名称
        cleaned_data['title'] = self._clean_text(job_data.get('title', ''))
        
        # 清洗公司名称
        cleaned_data['company'] = self._clean_text(job_data.get('company', ''))
        
        # 清洗地点
        cleaned_data['location'] = self._clean_location(job_data.get('location', ''))
        
        # 清洗薪资
        salary_min, salary_max = self._parse_salary(job_data.get('salary', ''))
        cleaned_data['salary_min'] = salary_min
        cleaned_data['salary_max'] = salary_max
        
        # 清洗学历要求
        cleaned_data['education'] = self._clean_education(job_data.get('education', ''))
        
        # 清洗经验要求
        cleaned_data['experience'] = self._clean_experience(job_data.get('experience', ''))
        
        # 清洗职位描述
        cleaned_data['description'] = self._clean_description(job_data.get('description', ''))
        
        # 标准化日期格式
        cleaned_data['posted_at'] = self._parse_date(job_data.get('posted_at', ''))
        cleaned_data['deadline'] = self._parse_date(job_data.get('deadline', ''))
        
        # 添加数据来源时间戳
        cleaned_data['crawled_at'] = datetime.now().isoformat()
        
        return cleaned_data
    
    def _clean_text(self, text: str) -> str:
        """清洗文本内容"""
        if not text:
            return ''
        
        # 移除多余空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除特殊字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text
    
    def _clean_location(self, location: str) -> str:
        """清洗地点信息"""
        if not location:
            return ''
        
        # 移除多余的地区信息
        location = re.sub(r'[·•].*$', '', location)
        location = re.sub(r'\s*-\s*.*$', '', location)
        
        return self._clean_text(location)
    
    def _parse_salary(self, salary_str: str) -> tuple:
        """解析薪资范围"""
        if not salary_str or '面议' in salary_str or '薪资面议' in salary_str:
            return None, None
        
        # 尝试各种薪资格式
        for pattern in self.salary_patterns:
            match = re.search(pattern, salary_str)
            if match:
                min_val, max_val = match.groups()
                
                # 转换为数字
                try:
                    min_salary = int(min_val)
                    max_salary = int(max_val)
                    
                    # 处理k和万的单位
                    if 'k' in salary_str.lower():
                        min_salary *= 1000
                        max_salary *= 1000
                    elif '万' in salary_str:
                        min_salary *= 10000
                        max_salary *= 10000
                    elif '千' in salary_str:
                        min_salary *= 1000
                        max_salary *= 1000
                    
                    return min_salary, max_salary
                except ValueError:
                    continue
        
        return None, None
    
    def _clean_education(self, education: str) -> str:
        """清洗学历要求"""
        if not education:
            return '不限'
        
        education = education.strip()
        
        # 查找匹配的学历
        for key, value in self.education_mapping.items():
            if key in education:
                return value
        
        return '不限'
    
    def _clean_experience(self, experience: str) -> str:
        """清洗经验要求"""
        if not experience:
            return '不限'
        
        experience = experience.strip()
        
        # 查找匹配的经验要求
        for key, value in self.experience_mapping.items():
            if key in experience:
                return value
        
        return '不限'
    
    def _clean_description(self, description: str) -> str:
        """清洗职位描述"""
        if not description:
            return ''
        
        # 移除HTML标签
        description = re.sub(r'<[^>]+>', '', description)
        
        # 移除多余的换行和空格
        description = re.sub(r'\n+', '\n', description)
        description = re.sub(r'\s+', ' ', description)
        
        return description.strip()
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        try:
            # 处理相对日期
            if '今天' in date_str or '刚刚' in date_str:
                return datetime.now().strftime('%Y-%m-%d')
            elif '昨天' in date_str:
                return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            elif '前天' in date_str:
                return (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
            elif '天前' in date_str:
                days = re.search(r'(\d+)天前', date_str)
                if days:
                    days_ago = int(days.group(1))
                    return (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            # 处理绝对日期
            date_patterns = [
                r'(\d{4})-(\d{1,2})-(\d{1,2})',
                r'(\d{4})/(\d{1,2})/(\d{1,2})',
                r'(\d{1,2})-(\d{1,2})-(\d{4})',
                r'(\d{1,2})/(\d{1,2})/(\d{4})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_str)
                if match:
                    groups = match.groups()
                    if len(groups[0]) == 4:  # YYYY-MM-DD format
                        year, month, day = groups
                    else:  # DD-MM-YYYY format
                        day, month, year = groups
                    
                    try:
                        date_obj = datetime(int(year), int(month), int(day))
                        return date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
        
        except Exception as e:
            logger.warning(f"日期解析失败: {date_str}, 错误: {e}")
        
        return None
    
    def validate_job_data(self, job_data: Dict) -> bool:
        """验证职位数据的完整性"""
        required_fields = ['title', 'company', 'source_id']
        
        for field in required_fields:
            if not job_data.get(field):
                logger.warning(f"职位数据缺少必要字段: {field}")
                return False
        
        return True
    
    def batch_clean(self, job_list: List[Dict]) -> List[Dict]:
        """批量清洗职位数据"""
        cleaned_jobs = []
        
        for job_data in job_list:
            try:
                cleaned_job = self.clean_job_data(job_data)
                if self.validate_job_data(cleaned_job):
                    cleaned_jobs.append(cleaned_job)
                else:
                    logger.warning(f"职位数据验证失败，跳过: {job_data.get('title', 'Unknown')}")
            except Exception as e:
                logger.error(f"数据清洗失败: {e}, 数据: {job_data}")
        
        logger.info(f"批量清洗完成，有效数据: {len(cleaned_jobs)}/{len(job_list)}")
        return cleaned_jobs
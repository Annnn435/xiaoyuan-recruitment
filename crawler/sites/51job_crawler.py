import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict
from bs4 import BeautifulSoup, element
from ..core.crawler_manager import BaseCrawler, CrawlerConfig

logger = logging.getLogger('51job_crawler')

class FiveOneJobCrawler(BaseCrawler):
    """前程无忧爬虫（企业级网站适配）"""
    name = "51job"
    url = "https://search.51job.com"
    
    def __init__(self, config: CrawlerConfig, proxy_pool=None, user_agent_pool=None):
        super().__init__(config, proxy_pool, user_agent_pool)
        self.base_url = "https://search.51job.com"
        self.detail_base_url = "https://jobs.51job.com"
    
    def _parse_job_list(self, html: str) -> List[Dict]:
        """解析职位列表页"""
        soup = BeautifulSoup(html, 'lxml')
        job_list = []
        
        # 找到职位列表容器
        job_items = soup.select('div.j_joblist > div.e > div.el')
        logger.info(f"Found {len(job_items)} job items on list page")
        
        for item in job_items:
            try:
                # 提取基本信息
                job_link = item.select_one('p.t1 > a')
                if not job_link:
                    continue
                
                job_name = job_link.get('title', '').strip()
                job_href = job_link.get('href', '')
                # 提取职位ID（用于去重）
                match = re.search(r'jobid=(\d+)', job_href)
                source_id = match.group(1) if match else None
                
                company_name = item.select_one('span.t2 > a').get('title', '').strip() if item.select_one('span.t2 > a') else ''
                location = item.select_one('span.t3').text.strip() if item.select_one('span.t3') else ''
                salary = item.select_one('span.t4').text.strip() if item.select_one('span.t4') else ''
                publish_date = item.select_one('span.t5').text.strip() if item.select_one('span.t5') else ''
                
                # 转换发布日期为标准格式
                try:
                    if '今天' in publish_date:
                        publish_date = datetime.now().strftime('%Y-%m-%d')
                    elif '昨天' in publish_date:
                        publish_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    else:
                        # 假设格式为 '08-29'
                        publish_date = f"{datetime.now().year}-{publish_date}"
                except Exception as e:
                    logger.warning(f"Failed to parse publish date: {publish_date}, error: {e}")
                    publish_date = datetime.now().strftime('%Y-%m-%d')
                
                job_data = {
                    'source': self.name,
                    'source_id': source_id,
                    'job_name': job_name,
                    'company_name': company_name,
                    'location': location,
                    'salary': salary,
                    'publish_date': publish_date,
                    'url': job_href,
                    'metadata': {
                        'salary': salary
                    }
                }
                
                job_list.append(job_data)
            except Exception as e:
                logger.error(f"Error parsing job item: {e}", exc_info=True)
                continue
        
        return job_list
    
    def _parse_job_detail(self, html: str, job_data: Dict) -> Dict:
        """解析职位详情页"""
        soup = BeautifulSoup(html, 'lxml')
        
        try:
            # 提取公司信息
            company_info = soup.select_one('div.cn > p.cname > a')
            if company_info:
                company_href = company_info.get('href', '')
                job_data['company_url'] = company_href
            
            # 提取公司类型、规模、行业
            company_attrs = soup.select('div.cn > p.msg.ltype')
            if company_attrs and len(company_attrs) > 0:
                attrs_text = company_attrs[0].get_text('\n', strip=True)
                attrs = [attr.strip() for attr in attrs_text.split('\n') if attr.strip()]
                
                if len(attrs) >= 3:
                    job_data['company_type'] = self._map_company_type(attrs[0])
                    job_data['company_size'] = attrs[1]
                    job_data['industry'] = attrs[2]
            
            # 提取职位信息
            job_info = soup.select('div.tCompany_main > div:nth-child(1) > div')
            if job_info:
                job_desc = job_info[0].get_text('\n', strip=True)
                job_data['description'] = job_desc
                
                # 尝试从描述中提取招聘类型
                recruitment_type = self._extract_recruitment_type(job_desc)
                if recruitment_type:
                    job_data['recruitment_type'] = recruitment_type
                
                # 尝试提取目标人群
                target_group = self._extract_target_group(job_desc)
                if target_group:
                    job_data['target_group'] = target_group
            
            # 提取截止日期
            deadline_elem = soup.select_one('div.tCompany_main > div:nth-child(2) > div > p:nth-child(2)')
            if deadline_elem:
                deadline_text = deadline_elem.get_text()
                match = re.search(r'截止日期：(.*)', deadline_text)
                if match:
                    deadline_str = match.group(1).strip()
                    try:
                        job_data['deadline'] = datetime.strptime(deadline_str, '%Y-%m-%d').isoformat()
                    except ValueError:
                        logger.warning(f"Cannot parse deadline: {deadline_str}")
            
            # 提取工作经验、学历要求等
            job_requirements = soup.select('div.cn > div.jd > p')
            if job_requirements:
                requirements_text = job_requirements[0].get_text('\n', strip=True)
                job_data['requirements'] = requirements_text
                
                # 提取到metadata中
                job_data['metadata']['requirements'] = requirements_text
        
        except Exception as e:
            logger.error(f"Error parsing job detail: {e}", exc_info=True)
        
        return job_data
    
    def _map_company_type(self, type_str: str) -> str:
        """映射公司类型到标准分类"""
        type_map = {
            '国企': '央国企',
            '上市公司': '民企',
            '外商独资': '外企',
            '中外合资': '外企',
            '事业单位': '事业单位',
            '银行': '银行',
            '民营公司': '民企',
            '跨国公司': '外企'
        }
        
        for key, value in type_map.items():
            if key in type_str:
                return value
        
        return type_str
    
    def _extract_recruitment_type(self, text: str) -> str:
        """从文本中提取招聘类型"""
        patterns = {
            '秋招': r'秋招|秋季招聘',
            '春招': r'春招|春季招聘',
            '补录': r'补录',
            '秋招提前批': r'秋招提前批|秋季提前批'
        }
        
        for type_name, pattern in patterns.items():
            if re.search(pattern, text):
                return type_name
        
        return '社会招聘'  # 默认值
    
    def _extract_target_group(self, text: str) -> str:
        """从文本中提取目标人群"""
        patterns = {
            '2024': r'2024届',
            '2025': r'2025届',
            '2026': r'2026届',
            '2027': r'2027届'
        }
        
        for group, pattern in patterns.items():
            if re.search(pattern, text):
                return group
        
        return '其他'
    
    def crawl(self, keyword: str = None) -> List[Dict]:
        """执行爬取"""
        all_jobs = []
        keyword = keyword or '校招'  # 默认爬取校招信息
        
        try:
            # 爬取前5页
            for page in range(1, 6):
                logger.info(f"Crawling 51job page {page} for keyword: {keyword}")
                
                # 构建搜索URL
                params = {
                    'keyword': keyword,
                    'searchType': '2',
                    'industryType': '',
                    'jobArea': '000000',
                    'jobType': '',
                    'salary': '',
                    'workYear': '',
                    'education': '',
                    'pageNum': page,
                    'lang': 'c',
                    'stype': '',
                    'postchannel': '0000',
                    'workId': '',
                    'requestId': '',
                    'scene': 'search',
                }
                
                # 抓取列表页
                html = self.fetch(self.base_url, params)
                
                # 解析列表页
                job_list = self._parse_job_list(html)
                if not job_list:
                    logger.info("No more jobs found, stopping crawl")
                    break
                
                # 抓取详情页
                for job in job_list:
                    # 检查去重
                    if self.is_duplicate(job.get('source_id')):
                        logger.debug(f"Duplicate job found: {job.get('source_id')}")
                        continue
                    
                    # 抓取详情
                    try:
                        detail_html = self.fetch(job.get('url', ''))
                        detailed_job = self._parse_job_detail(detail_html, job)
                        all_jobs.append(detailed_job)
                    except Exception as e:
                        logger.error(f"Failed to fetch detail for {job.get('url')}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Crawl failed: {e}", exc_info=True)
        
        return all_jobs

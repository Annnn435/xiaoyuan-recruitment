import os
import logging
import time
import random
from datetime import datetime
from typing import List, Dict, Type
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .proxy_pool import ProxyPool
from .user_agent_pool import UserAgentPool
from .data_cleaner import DataCleaner
from .exceptions import CrawlerException, RetryException

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('crawler_manager')

@dataclass
class CrawlerConfig:
    """爬虫配置项（企业级配置管理）"""
    max_retries: int = 3
    timeout: int = 10
    request_delay: float = 1.0  # 基础请求延迟
    max_concurrent: int = 5  # 最大并发数
    proxy_enabled: bool = True
    redis_url: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    db_url: str = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/recruitment')
    api_url: str = os.getenv('API_URL', 'http://localhost:5000/api/jobs')
    crawl_interval: int = 3600  # 爬取间隔（秒）

class BaseCrawler(ABC):
    """爬虫基类，定义标准接口"""
    name: str = "base"  # 爬虫名称
    url: str = ""  # 目标网站URL
    
    def __init__(self, config: CrawlerConfig, proxy_pool: ProxyPool = None, user_agent_pool: UserAgentPool = None):
        self.config = config
        self.proxy_pool = proxy_pool or ProxyPool()
        self.user_agent_pool = user_agent_pool or UserAgentPool()
        self.session = self._create_session()
        self.redis = redis.from_url(config.redis_url)
        self.data_cleaner = DataCleaner()
        
        # 创建数据库会话
        self.engine = create_engine(config.db_url)
        self.Session = sessionmaker(bind=self.engine)
    
    def _create_session(self) -> requests.Session:
        """创建带重试机制的请求会话（企业级网络请求可靠性）"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """获取随机请求头"""
        return {
            'User-Agent': self.user_agent_pool.get_random_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
        }
    
    def _get_proxy(self) -> Dict[str, str]:
        """获取代理（如果启用）"""
        if self.config.proxy_enabled:
            proxy = self.proxy_pool.get_proxy()
            if proxy:
                return {'http': proxy, 'https': proxy}
        return {}
    
    def fetch(self, url: str, params: Dict = None) -> str:
        """企业级网页抓取，带重试和反爬处理"""
        for attempt in range(self.config.max_retries):
            try:
                headers = self._get_headers()
                proxies = self._get_proxy()
                
                logger.info(f"Fetching {url} (attempt {attempt + 1}/{self.config.max_retries})")
                
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    proxies=proxies,
                    timeout=self.config.timeout,
                    allow_redirects=True
                )
                
                # 检查状态码
                response.raise_for_status()
                
                # 随机延迟，避免被识别为爬虫
                time.sleep(self.config.request_delay + random.uniform(0, 0.5))
                
                return response.text
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed: {str(e)}")
                
                # 标记可能失效的代理
                if proxies:
                    self.proxy_pool.mark_bad_proxy(next(iter(proxies.values())))
                
                if attempt < self.config.max_retries - 1:
                    # 指数退避重试
                    time.sleep(2 **attempt)
                    continue
                
                # 所有重试都失败
                raise RetryException(f"Failed to fetch {url} after {self.config.max_retries} attempts") from e
    
    def is_duplicate(self, source_id: str) -> bool:
        """检查是否已爬取过（基于Redis的去重机制）"""
        key = f"crawler:duplicate:{self.name}:{source_id}"
        return self.redis.exists(key)
    
    def mark_processed(self, source_id: str, ttl: int = 86400 * 7) -> None:
        """标记为已处理（7天过期）"""
        key = f"crawler:duplicate:{self.name}:{source_id}"
        self.redis.setex(key, ttl, 1)
    
    def save_to_database(self, job_data: List[Dict]) -> None:
        """保存数据到数据库（支持批量）"""
        if not job_data:
            return
        
        try:
            # 先尝试通过API保存（企业级数据流转）
            response = requests.post(
                f"{self.config.api_url}/batch",
                json={"jobs": job_data},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Saved {len(job_data)} jobs via API")
                return
        except Exception as e:
            logger.error(f"Failed to save via API: {str(e)}. Falling back to direct DB save.")
        
        # API失败时，直接保存到数据库
        session = self.Session()
        try:
            from ..models.job import Job  # 延迟导入，避免循环依赖
            
            for data in job_data:
                # 使用ORM的创建或更新方法
                job = Job.create_or_update(data)
                session.add(job)
                self.mark_processed(data.get('source_id'))
            
            session.commit()
            logger.info(f"Saved {len(job_data)} jobs directly to database")
        except Exception as e:
            session.rollback()
            logger.error(f"Database save failed: {str(e)}")
            raise
        finally:
            session.close()
    
    @abstractmethod
    def parse(self, html: str) -> List[Dict]:
        """解析网页内容，子类必须实现"""
        pass
    
    @abstractmethod
    def crawl(self, keyword: str = None) -> List[Dict]:
        """执行爬取，子类必须实现"""
        pass

class CrawlerManager:
    """爬虫管理器，协调多个爬虫工作（企业级任务调度）"""
    def __init__(self, config: CrawlerConfig = None):
        self.config = config or CrawlerConfig()
        self.proxy_pool = ProxyPool()
        self.user_agent_pool = UserAgentPool()
        self.crawlers: List[BaseCrawler] = []
        self.redis = redis.from_url(self.config.redis_url)
    
    def register_crawler(self, crawler_class: Type[BaseCrawler]) -> None:
        """注册爬虫"""
        crawler = crawler_class(
            config=self.config,
            proxy_pool=self.proxy_pool,
            user_agent_pool=self.user_agent_pool
        )
        self.crawlers.append(crawler)
        logger.info(f"Registered crawler: {crawler.name}")
    
    def run_crawler(self, crawler: BaseCrawler, keyword: str = None) -> List[Dict]:
        """运行单个爬虫"""
        try:
            logger.info(f"Starting crawler: {crawler.name} with keyword: {keyword or 'all'}")
            start_time = time.time()
            
            results = crawler.crawl(keyword)
            
            # 数据清洗（企业级数据质量保证）
            cleaned_results = [crawler.data_cleaner.clean(job) for job in results]
            
            # 去重
            unique_results = []
            for job in cleaned_results:
                source_id = job.get('source_id')
                if source_id and not crawler.is_duplicate(source_id):
                    unique_results.append(job)
            
            # 保存数据
            if unique_results:
                crawler.save_to_database(unique_results)
            
            elapsed = time.time() - start_time
            logger.info(
                f"Crawler {crawler.name} completed. "
                f"Found {len(results)}, Unique: {len(unique_results)}, "
                f"Time: {elapsed:.2f}s"
            )
            
            return unique_results
            
        except Exception as e:
            logger.error(f"Crawler {crawler.name} failed: {str(e)}", exc_info=True)
            return []
    
    def run_all(self, keyword: str = None, concurrent: bool = True) -> Dict[str, List[Dict]]:
        """运行所有爬虫，支持并发"""
        logger.info(f"Starting all crawlers with keyword: {keyword or 'all'}, concurrent: {concurrent}")
        results = {}
        
        if concurrent and len(self.crawlers) > 1:
            # 并发执行
            with ThreadPoolExecutor(max_workers=min(self.config.max_concurrent, len(self.crawlers))) as executor:
                futures = {
                    executor.submit(self.run_crawler, crawler, keyword): crawler.name
                    for crawler in self.crawlers
                }
                
                for future in as_completed(futures):
                    crawler_name = futures[future]
                    try:
                        results[crawler_name] = future.result()
                    except Exception as e:
                        logger.error(f"Future for {crawler_name} failed: {str(e)}")
        else:
            # 串行执行
            for crawler in self.crawlers:
                results[crawler.name] = self.run_crawler(crawler, keyword)
        
        # 统计总结果
        total = sum(len(items) for items in results.values())
        logger.info(f"All crawlers completed. Total unique jobs: {total}")
        
        # 记录最后运行时间
        self.redis.set("crawler:last_run", datetime.now().isoformat())
        
        return results
    
    def scheduled_run(self, keyword: str = None) -> None:
        """定时运行爬虫"""
        logger.info(f"Scheduled crawler run started with interval {self.config.crawl_interval}s")
        while True:
            self.run_all(keyword)
            logger.info(f"Next run in {self.config.crawl_interval}s")
            time.sleep(self.config.crawl_interval)

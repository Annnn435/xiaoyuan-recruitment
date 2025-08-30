import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crawler.core.crawler_manager import CrawlerConfig
from crawler.sites.51job_crawler import FiveOneJobCrawler
import json
from datetime import datetime

def test_51job_crawler():
    """测试前程无忧爬虫"""
    print("开始测试前程无忧爬虫...")
    
    # 创建配置（简化版，不使用Redis和数据库）
    config = CrawlerConfig(
        max_retries=2,
        timeout=15,
        request_delay=2.0,
        proxy_enabled=False,  # 暂时禁用代理
        redis_url='redis://localhost:6379/0',
        db_url='sqlite:///test.db'
    )
    
    # 创建爬虫实例
    crawler = FiveOneJobCrawler(config)
    
    try:
        # 爬取校招岗位
        print("正在爬取校招岗位...")
        jobs = crawler.crawl(keyword='校招')
        
        print(f"\n成功爬取到 {len(jobs)} 个岗位")
        
        # 筛选今天发布的岗位
        today = datetime.now().strftime('%Y-%m-%d')
        today_jobs = [job for job in jobs if job.get('publish_date') == today]
        
        print(f"今天发布的岗位数量: {len(today_jobs)}")
        
        # 显示前5个今天发布的岗位
        if today_jobs:
            print("\n=== 今天发布的岗位（前5个）===")
            for i, job in enumerate(today_jobs[:5], 1):
                print(f"{i}. {job.get('job_name', 'N/A')}")
                print(f"   公司: {job.get('company_name', 'N/A')}")
                print(f"   地点: {job.get('location', 'N/A')}")
                print(f"   薪资: {job.get('salary', 'N/A')}")
                print(f"   发布日期: {job.get('publish_date', 'N/A')}")
                print(f"   链接: {job.get('url', 'N/A')}")
                print("-" * 50)
        else:
            print("\n今天暂无新发布的岗位，显示最近的岗位:")
            for i, job in enumerate(jobs[:5], 1):
                print(f"{i}. {job.get('job_name', 'N/A')}")
                print(f"   公司: {job.get('company_name', 'N/A')}")
                print(f"   地点: {job.get('location', 'N/A')}")
                print(f"   薪资: {job.get('salary', 'N/A')}")
                print(f"   发布日期: {job.get('publish_date', 'N/A')}")
                print("-" * 50)
        
        # 保存结果到文件
        output_file = f"51job_crawl_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        
        print(f"\n爬取结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"爬取过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_51job_crawler()
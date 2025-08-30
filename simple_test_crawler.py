import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime, timedelta
import json

def simple_51job_test():
    """简化版前程无忧爬虫测试"""
    print("开始简化版前程无忧爬虫测试...")
    
    # 请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
    }
    
    # 搜索参数
    base_url = "https://search.51job.com/list/000000,000000,0000,00,9,99,%E6%A0%A1%E6%8B%9B,2,1.html"
    
    jobs = []
    
    try:
        print("正在请求前程无忧搜索页面...")
        response = requests.get(base_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"请求成功，状态码: {response.status_code}")
        
        # 解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找职位列表
        job_items = soup.select('div.j_joblist div.e div.el')
        if not job_items:
            # 尝试其他选择器
            job_items = soup.select('div.dw_table div.el')
        
        print(f"找到 {len(job_items)} 个职位项目")
        
        if len(job_items) == 0:
            print("未找到职位信息，可能页面结构已变化")
            print("页面标题:", soup.title.string if soup.title else "无标题")
            # 保存HTML用于调试
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("已保存页面HTML到 debug_page.html 用于调试")
            return
        
        # 解析每个职位
        for i, item in enumerate(job_items[:10]):  # 只取前10个
            try:
                # 职位名称和链接
                job_link = item.select_one('p.t1 a') or item.select_one('span.jname a')
                if not job_link:
                    continue
                
                job_name = job_link.get('title', job_link.text).strip()
                job_url = job_link.get('href', '')
                
                # 公司名称
                company_elem = item.select_one('span.t2 a') or item.select_one('span.cname a')
                company_name = company_elem.get('title', company_elem.text).strip() if company_elem else '未知公司'
                
                # 工作地点
                location_elem = item.select_one('span.t3') or item.select_one('span.area')
                location = location_elem.text.strip() if location_elem else '未知地点'
                
                # 薪资
                salary_elem = item.select_one('span.t4') or item.select_one('span.sal')
                salary = salary_elem.text.strip() if salary_elem else '面议'
                
                # 发布日期
                date_elem = item.select_one('span.t5') or item.select_one('span.time')
                publish_date = date_elem.text.strip() if date_elem else '未知时间'
                
                # 转换发布日期
                if '今天' in publish_date:
                    publish_date = datetime.now().strftime('%Y-%m-%d')
                elif '昨天' in publish_date:
                    publish_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                elif '-' in publish_date and len(publish_date.split('-')) == 2:
                    month, day = publish_date.split('-')
                    publish_date = f"{datetime.now().year}-{month.zfill(2)}-{day.zfill(2)}"
                
                job_data = {
                    'job_name': job_name,
                    'company_name': company_name,
                    'location': location,
                    'salary': salary,
                    'publish_date': publish_date,
                    'url': job_url
                }
                
                jobs.append(job_data)
                
            except Exception as e:
                print(f"解析第 {i+1} 个职位时出错: {e}")
                continue
        
        # 显示结果
        today = datetime.now().strftime('%Y-%m-%d')
        today_jobs = [job for job in jobs if job.get('publish_date') == today]
        
        print(f"\n总共解析到 {len(jobs)} 个职位")
        print(f"今天发布的职位: {len(today_jobs)} 个")
        
        print("\n=== 爬取到的职位信息 ===")
        for i, job in enumerate(jobs, 1):
            print(f"{i}. {job['job_name']}")
            print(f"   公司: {job['company_name']}")
            print(f"   地点: {job['location']}")
            print(f"   薪资: {job['salary']}")
            print(f"   发布日期: {job['publish_date']}")
            if job['publish_date'] == today:
                print("   ⭐ 今天发布")
            print("-" * 50)
        
        # 保存结果
        output_file = f"simple_crawl_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        
        print(f"\n结果已保存到: {output_file}")
        
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
    except Exception as e:
        print(f"爬取过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_51job_test()
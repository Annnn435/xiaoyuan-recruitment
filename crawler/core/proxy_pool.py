import logging
import random
import time
from typing import List, Dict, Optional
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = logging.getLogger('proxy_pool')

class ProxyPool:
    """代理池管理器 - 企业级代理管理"""
    
    def __init__(self, max_proxies: int = 100, check_interval: int = 300):
        self.max_proxies = max_proxies
        self.check_interval = check_interval
        self.proxies: List[Dict] = []
        self.lock = threading.Lock()
        self.last_check = 0
        
        # 免费代理源列表
        self.proxy_sources = [
            'https://www.proxy-list.download/api/v1/get?type=http',
            'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
        ]
        
        # 初始化代理池
        self._refresh_proxies()
    
    def _fetch_free_proxies(self) -> List[str]:
        """从免费代理源获取代理列表"""
        proxies = []
        
        for source in self.proxy_sources:
            try:
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    proxy_list = response.text.strip().split('\n')
                    proxies.extend([p.strip() for p in proxy_list if p.strip()])
                    logger.info(f"从 {source} 获取到 {len(proxy_list)} 个代理")
            except Exception as e:
                logger.warning(f"获取代理失败 {source}: {e}")
        
        return proxies[:self.max_proxies]
    
    def _test_proxy(self, proxy: str) -> Optional[Dict]:
        """测试代理可用性"""
        test_url = 'http://httpbin.org/ip'
        proxy_dict = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        try:
            start_time = time.time()
            response = requests.get(
                test_url, 
                proxies=proxy_dict, 
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            if response.status_code == 200:
                response_time = time.time() - start_time
                return {
                    'proxy': proxy,
                    'response_time': response_time,
                    'last_used': 0,
                    'success_count': 0,
                    'fail_count': 0,
                    'status': 'active'
                }
        except Exception as e:
            logger.debug(f"代理测试失败 {proxy}: {e}")
        
        return None
    
    def _refresh_proxies(self):
        """刷新代理池"""
        logger.info("开始刷新代理池...")
        
        # 获取免费代理
        proxy_list = self._fetch_free_proxies()
        
        # 并发测试代理
        valid_proxies = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_proxy = {executor.submit(self._test_proxy, proxy): proxy for proxy in proxy_list}
            
            for future in as_completed(future_to_proxy):
                result = future.result()
                if result:
                    valid_proxies.append(result)
                    if len(valid_proxies) >= self.max_proxies:
                        break
        
        with self.lock:
            self.proxies = valid_proxies
            self.last_check = time.time()
        
        logger.info(f"代理池刷新完成，可用代理数量: {len(valid_proxies)}")
    
    def get_proxy(self) -> Optional[Dict]:
        """获取一个可用代理"""
        # 检查是否需要刷新代理池
        if time.time() - self.last_check > self.check_interval:
            self._refresh_proxies()
        
        with self.lock:
            if not self.proxies:
                return None
            
            # 选择响应时间最快且最少使用的代理
            available_proxies = [p for p in self.proxies if p['status'] == 'active']
            if not available_proxies:
                return None
            
            # 按响应时间和使用次数排序
            proxy = min(available_proxies, key=lambda x: (x['last_used'], x['response_time']))
            proxy['last_used'] = time.time()
            
            return {
                'http': f"http://{proxy['proxy']}",
                'https': f"http://{proxy['proxy']}"
            }
    
    def mark_proxy_failed(self, proxy_dict: Dict):
        """标记代理失败"""
        if not proxy_dict:
            return
            
        proxy_str = proxy_dict.get('http', '').replace('http://', '')
        
        with self.lock:
            for proxy in self.proxies:
                if proxy['proxy'] == proxy_str:
                    proxy['fail_count'] += 1
                    if proxy['fail_count'] >= 3:
                        proxy['status'] = 'inactive'
                    break
    
    def mark_proxy_success(self, proxy_dict: Dict):
        """标记代理成功"""
        if not proxy_dict:
            return
            
        proxy_str = proxy_dict.get('http', '').replace('http://', '')
        
        with self.lock:
            for proxy in self.proxies:
                if proxy['proxy'] == proxy_str:
                    proxy['success_count'] += 1
                    proxy['fail_count'] = max(0, proxy['fail_count'] - 1)
                    break
    
    def get_stats(self) -> Dict:
        """获取代理池统计信息"""
        with self.lock:
            active_count = len([p for p in self.proxies if p['status'] == 'active'])
            return {
                'total_proxies': len(self.proxies),
                'active_proxies': active_count,
                'inactive_proxies': len(self.proxies) - active_count,
                'last_refresh': self.last_check
            }
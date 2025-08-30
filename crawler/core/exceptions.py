class CrawlerException(Exception):
    """爬虫基础异常类"""
    pass

class RetryException(CrawlerException):
    """需要重试的异常"""
    pass

class ProxyException(CrawlerException):
    """代理相关异常"""
    pass

class ParseException(CrawlerException):
    """数据解析异常"""
    pass

class RateLimitException(CrawlerException):
    """请求频率限制异常"""
    pass

class BlockedException(CrawlerException):
    """IP被封禁异常"""
    pass
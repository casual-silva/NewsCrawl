# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import logging
import requests

from scrapy import signals
from scrapy.exceptions import IgnoreRequest
from .package.bloom_redis import BloomFilter

from .package.spider_proxy import proxy_list, get_proxies
from .settings import BIND_PROXY_API
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
from twisted.internet.error import ConnectionRefusedError, TimeoutError


class MyRetryMiddleware(RetryMiddleware):
    '''
    代理中间件, 请求失败时可重试
    '''
    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.bind_ip()

    def bind_ip(self):
        bind_api = BIND_PROXY_API
        rsp = requests.get(bind_api).json()
        self.logger.warning(rsp)

    def _delete_proxy(self, proxy=None):
        if proxy in proxy_list:
            proxy_list.remove(proxy)

    def process_request(self, request, spider):
        proxy = get_proxies()
        self.logger.warning('request.url: {0} 使用代理：{1}'.format(request.url, proxy))
        request.meta["proxy"] = proxy


    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            # 删除该代理
            self._delete_proxy(request.meta.get('proxy', False))
            self.logger.warning('返回值异常, 进行重试...')
            return self._retry(request, reason, spider) or response
        return response


    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) \
                and not request.meta.get('dont_retry', False):
            # 删除该代理
            self._delete_proxy(request.meta.get('proxy', False))
            self.logger.warning('连接异常: {} ; 进行重试...'.format(str(exception)))
            return self._retry(request, exception, spider)



# 抓取前在 process_request 判断是否需要去重
class TlnewsspiderDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
        self.bloom = BloomFilter()

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        '''
        此处用来进行详情页抓取去重, 避免多余重复请求造成资源浪费
        '''
        # 判断当前链接是否已存在
        # print(">>", "process_request _url", request._url)
        if request._url and self.bloom.isContains(request._url):
            spider.logger.info(f'>> 重复的连接去重: {request._url}')
            raise IgnoreRequest(f'>> 重复的连接去重: {request._url}')
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass



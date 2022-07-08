# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time

from ..utils import date
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class QqComSpider(scrapy.Spider):
    name = 'qq.com'
    # allowed_domains = ['qq.com']
    site_name = '腾讯网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 财经 > 产业公司", "https://new.qq.com/ch2/cyxw"],
        ["宏观舆情", "首页 > 财经 > 宏观经济", "https://new.qq.com/ch2/hgjj"],
        ["行业舆情", "首页 > 财经 > 银行", "https://new.qq.com/ch2/yinhang"],
        ["行业舆情", "首页 > 财经新闻 > 最新资讯", "https://new.qq.com/ch/finance/"],
        ["行业舆情", "首页 > 财经 > 基金", "https://new.qq.com/ch2/jijin"],
        ["企业舆情", "首页 > 汽车 > 行业热点", "https://new.qq.com/ch2/hyrd"]
    ]

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'qq.com/ch2/cyxw' in response.url:
            for i in range(0,20):
               url=f"https://pacaio.match.qq.com/irs/rcd?cid=52&token=8f6b50e1667f130c10f981309e1d8200&ext=3913,3914,3915,&page={i}&isForce=1"
               yield scrapy.Request(url=url, callback=self.parse_qq, meta=response.meta)

        elif 'ch2/hgjj' in response.url:
            for i in range(0, 50):
                url = f"https://pacaio.match.qq.com/irs/rcd?cid=52&token=8f6b50e1667f130c10f981309e1d8200&ext=3909,3916&page={i}&isForce=1"
                yield scrapy.Request(url=url, callback=self.parse_qq, meta=response.meta)
                
        elif 'qq.com/ch2/yinhang' in response.url:
            for i in range(0, 50):
                url = f"https://pacaio.match.qq.com/irs/rcd?cid=52&token=8f6b50e1667f130c10f981309e1d8200&ext=3901,3902,3903,3917&page={i}&isForce=1"
                yield scrapy.Request(url=url, callback=self.parse_qq, meta=response.meta)
                
        elif 'qq.com/ch/finance/' in response.url:
            for i in range(0, 200,10):
                code='{%22pool%22%3A%5B%22hot%22%5D,%22is_filter%22%3A2,%22check_type%22%3Atrue}'
                url=f"https://i.news.qq.com/trpc.qqnews_web.kv_srv.kv_srv_http_proxy/list?sub_srv_id=finance&srv_id=pc&offset={i}&limit=20&strategy=1&ext={code}"
                yield scrapy.Request(url=url,callback=self.parse_finance, meta=response.meta)
                
        elif 'qq.com/ch2/jijin' in response.url:
            for i in range(0, 100):
                url = f"https://pacaio.match.qq.com/irs/rcd?cid=52&token=8f6b50e1667f130c10f981309e1d8200&ext=3904,3908,3910&page={i}&isForce=1"
                yield scrapy.Request(url=url, callback=self.parse_qq, meta=response.meta)
                
        elif 'qq.com/ch2/hyrd' in response.url:
            for i in range(0, 50):
                url = f"https://pacaio.match.qq.com/irs/rcd?cid=52&token=8f6b50e1667f130c10f981309e1d8200&ext=4203,4205&page={i}&isForce=1"
                yield scrapy.Request(url=url, callback=self.parse_qq, meta=response.meta)

    # 首页 - 保险 - 行业公司
    def parse_qq(self, response):
        data=json.loads(response.text).get('data')
        for d in data:
            url=d.get('vurl')
            response.meta['source']=d.get('source')
            response.meta['publish_time'] = d.get('publish_time')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
            
    def parse_finance(self,response):
        data=json.loads(response.text).get('data')
        list=data.get('list')
        for li in list:
            url=li.get('url')
            response.meta['source'] = li.get('media_name')
            response.meta['publish_time'] = li.get('publish_time')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', response.meta['publish_time'])  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_value('article_source', response.meta['source'])  # 来源/article_source
        item.add_value('author',self.author_rules.extractor(response.text))  # 作者/author
        # 默认保存一般无需更改
        item.add_value('spider_time', date())  # 抓取时间
        item.add_value('created_time', date())  # 更新时间
        item.add_value('source_url', response.url)  # 详情网址/detail_url
        item.add_value('site_name', self.site_name)  # 站点名称
        item.add_value('site_url', urlsplit(response.url).netloc)  # 站点host
        item.add_value('classification', response.meta['classification'])  # 所属分类
        # 网页源码  调试阶段注释方便查看日志
        # item.add_value('html_text', response.text)  # 网页源码

        # 上面获取值可能为空, 追加匹配值
        # item.add_xpath('title', '//h1/text() || //p/h5/text()', re='[标题]{2}:(.*?)')  # 标题/title
        # item.add_css('publish_date', 'p:nth-last-child(-n+5)', re="[0-9]{0,4}年[0-9]{1,2}月[0-9]{1,2}日")  # 发布日期/publish_date
        return item.load_item()

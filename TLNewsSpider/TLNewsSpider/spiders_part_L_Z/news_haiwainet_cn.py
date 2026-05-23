# -*- coding: utf-8 -*-

import re
import math
import scrapy
import json
from urllib.parse import urlsplit

from ..utils import date, over_page, date2time
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class NewsHaiwainetCnSpider(scrapy.Spider):
    name = 'news.haiwainet.cn'
    allowed_domains = ['haiwainet.cn']
    site_name = '海外网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["宏观舆情", "首页>资讯", "http://news.haiwainet.cn/"],
        ["宏观舆情", "首页 > 华媒 > 聚商业", "http://huamei.haiwainet.cn/"]
        
    ]

    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            #若不需要用到num来传递次数，则可删去
            meta = {'classification': classification,'num':0}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'news.haiwainet' in response.url:
            for i in range(1,121):
                url=f"https://opa.haiwainet.cn/apis/news?page={i}&num=20&moreinfo=1&order=1&catid=3541085"
                yield from over_page(url,response,page_num=i,callback=self.parse_jijing)
                
        elif 'huamei.haiwainet' in response.url:
            url="http://opa.haiwainet.cn/apis/news&moreinfo=1&catid=3541220&num=10&page=1"
            yield from over_page(url,response,page_num=1,callback=self.parse_jijing)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        result=json.loads(response.text).get('result')
        for data in result:
            link=data.get('link')
            pubtime=data.get('pubtime')
            source=data.get('source')
            response.meta['source']=source
            response.meta['pubtime'] = pubtime
            pt=date2time(time_str=pubtime)
            yield from over_page(link,response,page_num=1,page_time=pt,callback=self.parse_detail)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', response.meta['pubtime'])  # 发布日期/publish_date
        item.add_xpath('content_text','//*[@class="contentMain"]/p//text()')  # 正文内容/text_content
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
        item.add_value('html_text', response.text)  # 网页源码
        return item.load_item()

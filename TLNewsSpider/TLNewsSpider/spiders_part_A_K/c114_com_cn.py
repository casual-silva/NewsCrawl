# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time

from ..utils import date, over_page
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class C114ComCnSpider(scrapy.Spider):
    name = 'c114.com.cn'
    allowed_domains = ['c114.com.cn']
    site_name = 'C114通信网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 新闻", "https://www.c114.com.cn/news/"],
        ["行业舆情", "首页 > 安防", "https://www.c114.com.cn/anfang/"],
        ["行业舆情", "首页 > 人工智能", "https://www.c114.com.cn/ai/"],
        ["行业舆情", "首页 > 云计算", "https://www.c114.com.cn/cloud/"],
        ["企业舆情", "首页 > 运营商动态 > 最新动态", "http://www.c114.com.cn/local/"]
    ]
    
    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification,'num':0}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if '/news/' in response.url:
            for y in range(2018,2023):
                for m in range(1,13):
                    for d in range(1,32):
                        response.meta['num'] += 1
                        data={'y':str(y),'m': str(m),'d': str(d)}
                        url='https://www.c114.com.cn/news/roll.asp'
                        yield from over_page(url, response, callback=self.parse_news,formdata=data,
                                             page_num=response.meta['num'])
                        # yield scrapy.FormRequest(url,callback=self.parse_news,meta=response.meta,formdata=data)

        elif 'anfang' in response.url:
            response.meta['code']='4324'
            yield from self.parse_c114(response)
            
        elif '/ai/' in response.url:
            response.meta['code']='5339'
            yield from self.parse_c114(response)
            
        elif 'cloud/' in response.url:
            response.meta['code']='4049'
            yield from self.parse_c114(response)
            
        elif 'local/' in response.url:
            response.meta['code']='117,118,119,4564,4329,4330,4331,4332'
            yield from self.parse_local(response)

    def parse_c114(self, response):
        for url in response.css(".new_list_c a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        for i in range(2,500):
            url_next=f"https://www.c114.com.cn/api/ajax/aj_1805_2.asp?p={i}&idn={response.meta['code']}"
            yield from over_page(url_next, response, page_num=i, callback=self.parse_news)

    def parse_local(self, response):
        for url in response.css(".newsText a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        for i in range(2,500):
            url_next=f"https://www.c114.com.cn/api/ajax/aj_1805_2.asp?p={i}&idn={response.meta['code']}"
            yield from over_page(url_next, response, page_num=i, callback=self.parse_news)
            
    def parse_news(self, response):
        # print(response.text)
        for url in response.css(".new_list_c a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        pd=self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('/','-')
        item.add_value('publish_date',publish_date)  # 发布日期/publish_date
        content=response.xpath('//*[@class="text"]//p//text()').getall()
        content_text=[x.strip() for x in content if x.strip() != '']
        item.add_value('content_text',content_text)  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//div[@class="author"]//text()')  # 来源/article_source
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

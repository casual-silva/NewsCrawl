# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time

from ..utils import date, over_page,date2time
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class CapcOrgCnSpider(scrapy.Spider):
    name = 'capc.org.cn'
    allowed_domains = ['capc.org.cn']
    site_name = '中国医药商业协会'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 行业动态", "http://www.capc.org.cn/index.html/list-973584c8ac764238a5af133c5561f351.html"],
        ["行业舆情", "首页>行业动态>行业信息", "http://www.capc.org.cn/index.html/list-e0978628ef66490a916a3b66017bdd39.html"]
    ]
    
    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'list-973584c8ac764238a5af133c5561f351.html' in response.url:
            for i in range(1,200):
                url=f"http://www.capc.org.cn/index.html/list-50b8ad66070d4e729b1389985abe9edd.html?pageNo={i}&pageSize=4"
                yield from over_page(url, response, page_num=i, callback=self.parse_capc)

        elif 'list-e0978628ef66490a916a3b66017bdd39.html' in response.url:
            for i in range(1, 200):
                url = f"http://www.capc.org.cn/index.html/list-e0978628ef66490a916a3b66017bdd39.html?pageNo={i}&pageSize=4"
                yield from over_page(url, response, page_num=i, callback=self.parse_capc)

    def parse_capc(self, response):
        for data in response.xpath('//*[@class="list_a"]/a'):
            data_url=data.xpath('./@hrf').get()
            data_time=data.xpath('.//*[@class="list_time"]/text()').get()
            url=f"http://www.capc.org.cn{data_url}"
            pagetime=date2time(date_str=data_time)
            yield from over_page(url,response,callback=self.parse_detail,page_time=pagetime)
            
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title','//*[@class="list_a"]/h2/text()')  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        content=response.xpath( '//*[@class="newxw"]/p//text()').getall()
        content_text=[x.strip() for x in content if x.strip() != '']
        item.add_value('content_text', content_text)  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="layuan"]/text()')  # 来源/article_source
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

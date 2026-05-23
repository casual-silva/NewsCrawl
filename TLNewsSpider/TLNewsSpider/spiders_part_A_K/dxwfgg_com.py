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



class DxwfggComSpider(scrapy.Spider):
    name = 'dxwfgg.com'
    allowed_domains = ['dxwfgg.com']
    site_name = '长垣万全商务网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页>机械设备", "http://changyuan.dxwfgg.com/list-12.html"],
        ["企业舆情", "首页>电工电气", "http://changyuan.dxwfgg.com/list-6.html"],
        ["企业舆情", "首页>仪器仪表", "http://changyuan.dxwfgg.com/list-9.html"],
        ["企业舆情", "首页>五金配件", "http://changyuan.dxwfgg.com/list-8.html"],
        ["企业舆情", "首页>化工材料", "http://changyuan.dxwfgg.com/list-26.html"],
        ["企业舆情", "首页>商业服务", "http://changyuan.dxwfgg.com/list-35.html"],
        ["企业舆情", "首页>建筑建材", "http://changyuan.dxwfgg.com/list-30.html"],
        ["企业舆情", "首页>冶金矿产", "http://changyuan.dxwfgg.com/list-33.html"]
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
        #直接在parse里遍历页码的翻页
        if '/list-12.html' in  response.url:
           for i in range(1,31):
               url=f"http://changyuan.dxwfgg.com/list-12-{i}.html"
               yield scrapy.Request(url,callback=self.parse_jijing,meta=response.meta)
               
        elif '/list-6.html' in  response.url:
           for i in range(1,31):
               url=f"http://changyuan.dxwfgg.com/list-6-{i}.html"
               yield scrapy.Request(url,callback=self.parse_jijing,meta=response.meta)
               
        elif '/list-9.html' in  response.url:
           for i in range(1,31):
               url=f"http://changyuan.dxwfgg.com/list-9-{i}.html"
               yield scrapy.Request(url,callback=self.parse_jijing,meta=response.meta)
               
        elif '/list-8.html' in  response.url:
           for i in range(1,11):
               url=f"http://changyuan.dxwfgg.com/list-8-{i}.html"
               yield scrapy.Request(url,callback=self.parse_jijing,meta=response.meta)
               
        elif '/list-26.html' in  response.url:
           for i in range(1,31):
               url=f"http://changyuan.dxwfgg.com/list-26-{i}.html"
               yield scrapy.Request(url,callback=self.parse_jijing,meta=response.meta)
               
        elif '/list-35.html' in  response.url:
           for i in range(1,61):
               url=f"http://changyuan.dxwfgg.com/list-35-{i}.html"
               yield scrapy.Request(url,callback=self.parse_jijing,meta=response.meta)
               
        elif '/list-30.html' in  response.url:
           for i in range(1,31):
               url=f"http://changyuan.dxwfgg.com/list-30-{i}.html"
               yield scrapy.Request(url,callback=self.parse_jijing,meta=response.meta)
               
        elif '/list-33.html' in  response.url:
           for i in range(1,31):
               url=f"http://changyuan.dxwfgg.com/list-33-{i}.html"
               yield scrapy.Request(url,callback=self.parse_jijing,meta=response.meta)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        for data in response.xpath('//*[@class="list shadow"]/ul/li'):
            data_url=data.xpath('./a/@href').get()
            data_time=data.xpath('./span/text()').get()
            pagetime=date2time(date_str=data_time)
            yield from over_page(data_url,response,page_num=1,page_time=pagetime,callback=self.parse_detail)


    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
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

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



class ZhidxComSpider(scrapy.Spider):
    name = 'zhidx.com'
    allowed_domains = ['zhidx.com']
    site_name = '智东西'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页>人工智能", "https://zhidx.com/p/category/%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD"],
        ["行业舆情", "首页>AI芯片", "https://zhidx.com/p/category/series-article/aichip"],
        ["行业舆情", "首页>AIoT", "https://zhidx.com/p/category/intelligent-home"],
        ["宏观舆情", "首页>新基建", "https://zhidx.com/p/category/digital-new-capital-construction"],
        ["行业舆情", "首页>机器人", "https://zhidx.com/p/category/%E6%9C%BA%E5%99%A8%E4%BA%BA%E6%97%A0%E4%BA%BA%E6%9C%BA"],
        ["行业舆情", "首页>VR/AR", "https://zhidx.com/p/category/virtualreality"]
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
        for url in response.css(".info-left-title a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        pd=self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('/','-')
        item.add_value('publish_date',publish_date )  # 发布日期/publish_date
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

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



class MbahomeComSpider(scrapy.Spider):
    name = 'mbahome.com'
    allowed_domains = ['mbahome.com']
    site_name = '商业中国网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页>金融", "http://www.mbahome.com/jinrong/"],
        ["企业舆情", "首页>汽车", "http://www.mbahome.com/qiche/"],
        ["企业舆情", "首页>楼市", "http://www.mbahome.com/loushi/"],
        ["宏观舆情", "首页>互联网", "http://www.mbahome.com/hulianwang/"],
        ["宏观舆情", "首页>财经", "http://finance.mbahome.com/"],
        ["宏观舆情", "首页>聚焦", "http://www.mbahome.com/jujiao/"],
        ["宏观舆情", "首页>市场", "http://www.mbahome.com/shichang/"],
        ["宏观舆情", "首页>产品", "http://www.mbahome.com/chanpin/"],
        ["宏观舆情", "首页>焦点", "http://www.mbahome.com/newss/jiaodian/"],
        ["企业舆情", "首页>新闻", "http://news.mbahome.com/"]
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
        for url in response.css(".datatit a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
            
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title', '//*[@id="title"]/text()')  # 标题/title
        item.add_xpath('publish_date','//*[@id="pubtime_baidu"]/text()')  # 发布日期/publish_date
        item.add_xpath('content_text', '//*[@class="TRS_Editor"]/p[not(@style)]//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@id="source_baidu"]/text()',re='来源： (.*)')  # 来源/article_source
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

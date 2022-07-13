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



class CfenComCnSpider(scrapy.Spider):
    name = 'cfen.com.cn'
    allowed_domains = ['cfen.com.cn']
    site_name = '中国财经报网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["宏观舆情", "首页>新闻>财政", "http://www.cfen.com.cn/cjxw/cz/"],
        ["宏观舆情", "首页>新闻>金融", "http://www.cfen.com.cn/cjxw/jr/"],
        ["行业舆情", "首页>新闻>产业", "http://www.cfen.com.cn/cjxw/cy/"],
        ["地区舆情", "首页>新闻>地方", "http://www.cfen.com.cn/cjxw/df/"]
    ]
    
    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification,'url':url,'num':0}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        for data in response.xpath('//*[@class="main_left_m1"]'):
            data_url=data.xpath('.//*[@class="title"]/@href').get()
            data_time=data.xpath('.//*[@class="b1"][last()]/text()').get()
            data_url_=data_url.replace('./','')
            data_time_=data_time.replace('发布时间：','')
            url=f"{response.meta['url']}{data_url_}"
            pagetime=date2time(date_str=data_time_)
            yield from over_page(url,response,page_time=pagetime,callback=self.parse_detail)

        # 翻页
        response.meta['num']+=1
        code=f"{response.meta['url']}index_{response.meta['num']}.html"
        yield from over_page(code, response,page_time=pagetime, callback=self.parse)
        
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="main_s"]/h4/text()',re='来源：(.*) ')  # 来源/article_source
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
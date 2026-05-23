# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time

from ..utils import date,over_page
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class HongzhoukanComSpider(scrapy.Spider):
    name = 'hongzhoukan.com'
    allowed_domains = ['hongzhoukan.com']
    site_name = '证券市场红周刊'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "红周刊首页 > 公司巡礼", "http://static.hongzhoukan.com/xblm/gsxl_323/list.html"],
        ["企业舆情", "红周刊首页 > 公司透析", "http://static.hongzhoukan.com/xblm/gstx_394/list.html"]
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
        if 'gsxl_323/list.html' in response.url:
            for i in range(0,21):
                url=f"http://static.hongzhoukan.com/xblm/gsxl_323/NewsList_{i}.json"
                yield from over_page(url,response,page_num=i,callback=self.parse_List)

        elif 'gstx_394/list.html' in response.url:
            for i in range(0,21):
                url = f"http://static.hongzhoukan.com/xblm/gstx_394/NewsList_{i}.json"
                yield from over_page(url,response,page_num=i,callback=self.parse_List)

    # 首页 - 保险 - 行业公司
    def parse_List(self, response):
        info=json.loads(response.text).get('info')
        for inf in info:
            url=inf.get('url')
            response.meta['issueTime']=inf.get('issueTime')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', response.meta['issueTime'])  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="author"][1]//text()',re='来源：(.*)')  # 来源/article_source
        item.add_xpath('article_source', '//*[@class="author"][1]/a/text()')
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

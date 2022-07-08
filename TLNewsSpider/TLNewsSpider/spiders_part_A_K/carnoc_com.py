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



class CarnocComSpider(scrapy.Spider):
    name = 'carnoc.com'
    allowed_domains = ['carnoc.com']
    site_name = '民航资源网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页>资讯", "http://www.carnoc.com/fast_news/fast_news.html#cate=0"]
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
        url='https://service.carnoc.com/sentiment/index.php/flash/list/index?limit=30&cate=0'
        yield scrapy.Request(url,callback=self.parse_jijing,meta=response.meta)
        
    def parse_jijing(self, response):
        list=json.loads(response.text).get('list')
        lis=list.get('list')
        for li in lis:
            url=li.get('url')
            sendTime=li.get('sendTime')
            yield from over_page(url,response,page_time=int(sendTime),callback=self.parse_detail)

        # 翻页
        next_url=f"https://service.carnoc.com/sentiment/index.php/flash/list/index?lt={sendTime}&limit=30&cate=3"
        response.meta['num'] += 1
        yield from over_page(next_url, response, page_time=int(sendTime), page_num=response.meta['num'], callback=self.parse_jijing)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text', '//*[@id="newstext"]/p/text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@id="source_baidu"]/a/text()')  # 来源/article_source
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

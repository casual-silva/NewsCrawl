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



class ElecfansComSpider(scrapy.Spider):
    name = 'elecfans.com'
    allowed_domains = ['elecfans.com']
    site_name = '电子发烧友'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页>行业新闻", "http://www.elecfans.com/news/hangye/"],
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

        for data in response.xpath('//*[@class="article-list"]'):
            url=data.xpath('.//*[@class="a-title"]/a/@href').get()
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页 非标准时间排序，无法根据时间进行限制
        page=response.xpath('//*[@class="page-next"]/@href').get()
        next_url=f"http://www.elecfans.com/news/hangye/{page}"
        response.meta['num'] += 1
        yield from over_page(next_url, response, page_num=response.meta['num'], callback=self.parse)
   
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        content=response.xpath('//*[@class="simditor-body clearfix"]/p//text()').getall()
        if content != []:
            content_text=[x.strip() for x in content if x.strip() != '']
            item.add_value('content_text',content_text )  # 正文内容/text_content
        else:
            item.add_value('content_text', content_rules.extract(response.text))
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="article-info art-share-layout m-share-layout clearfix"]/span[not(@class)][1]/text()',re='来源：(.*)')  # 来源/article_source
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

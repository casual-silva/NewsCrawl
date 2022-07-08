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



class CheaaComSpider(scrapy.Spider):
    name = 'cheaa.com'
    allowed_domains = ['cheaa.com']
    site_name = '中国家电网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 新闻中心 > 行业新闻", "http://news.cheaa.com/hangye.shtml"],
        ["企业舆情", "首页 > 新闻中心 > 上市企业", "http://news.cheaa.com/shangshi.shtml"],
        ["企业舆情", "首页 > 新闻中心 > 上游资讯", "http://news.cheaa.com/shangyou.shtml"],
        ["企业舆情", "首页 > 新闻中心 > 渠道资讯", "http://news.cheaa.com/qudao.shtml"]
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
        for url in response.css(".pctit a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        page=response.xpath('//a[@class="next"]/@href').get()
        response.meta['num'] +=1
        yield from over_page(page, response, page_num=response.meta['num'], callback=self.parse)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="info"]/text()',re='来源：(.*)\xa0')
        item.add_xpath('article_source', '//*[@class="info"]/text()',re='来源：(.*)')  # 来源/article_source
        item.add_xpath('author','//*[@class="info"]/a/text()')  # 作者/author
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

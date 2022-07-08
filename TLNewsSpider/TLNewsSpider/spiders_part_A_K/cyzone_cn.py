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


class CyzoneCnSpider(scrapy.Spider):
    name = 'cyzone.cn'
    allowed_domains = ['cyzone.cn']
    site_name = '创业邦'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 资讯>汽车", "https://www.cyzone.cn/content/channel/index?channel_id=8"],
        ["行业舆情", "首页 > 资讯>医疗", "https://www.cyzone.cn/content/channel/index?channel_id=27"],
        ["行业舆情", "首页 > 资讯>文娱", "https://www.cyzone.cn/content/channel/index?channel_id=11"],
        ["行业舆情", "首页 > 资讯>科技股", "https://www.cyzone.cn/content/channel/index?channel_id=33"]
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
        if 'channel_id=8' in response.url:
            for i in range(1, 100):
                url = f"https://www.cyzone.cn/api/v2/content/channel/detail?page={i}&channel_id=8"
                yield from over_page(url, response, page_num=i, callback=self.parse_channel)

        elif 'channel_id=27' in response.url:
            for i in range(1, 100):
                url = f"https://www.cyzone.cn/api/v2/content/channel/detail?page={i}&channel_id=27"
                yield from over_page(url, response, page_num=i, callback=self.parse_channel)

        elif 'channel_id=11' in response.url:
            for i in range(1, 100):
                url = f"https://www.cyzone.cn/api/v2/content/channel/detail?page={i}&channel_id=11"
                yield from over_page(url, response, page_num=i, callback=self.parse_channel)

        elif 'channel_id=33' in response.url:
            for i in range(1, 100):
                url = f"https://www.cyzone.cn/api/v2/content/channel/detail?page={i}&channel_id=33"
                yield from over_page(url, response, page_num=i, callback=self.parse_channel)


    # 首页 - 保险 - 行业公司
    def parse_channel(self, response):
        data = json.loads(response.text).get('data')
        for d in data:
            url = d.get('url')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_css('article_source', '.source .ly a:first-child::text')  # 来源/article_source
        item.add_value('author', self.author_rules.extractor(response.text))  # 作者/author
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

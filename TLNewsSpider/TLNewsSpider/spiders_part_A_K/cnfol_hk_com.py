# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit

from ..utils import date, over_page
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor
import time
import json


class CnfolHkComSpider(scrapy.Spider):
    name = 'cnfol.hk.com'
    site_name = '中金在线'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 >港股> 新闻 > 市场分析", "http://www.cnfol.hk/news/ganggujujiao/"],
        ["企业舆情", "首页 >港股> 新闻 > 港股要闻", "http://www.cnfol.hk/news/gangguzx/"],
        ["企业舆情", "首页 >港股> 新闻 > 个股评级", "http://www.cnfol.hk/news/dahangtuijian/"],
        ["企业舆情", "首页 >港股> 新闻 > 宏观财经", "http://www.cnfol.hk/news/gncaijing/"],
        ["企业舆情", "首页 >港股> 新闻 > 新股资讯", "http://www.cnfol.hk/ipo/"],
        ["企业舆情", "首页 >港股> 新闻 > 沪/深港通资讯", "http://www.cnfol.hk/shhkc/"],
        ["企业舆情", "首页 >港股> 新闻 > 港股学堂", "http://www.cnfol.hk/news/gangguxuetang/"],
        ["企业舆情", "首页 >港股> 新闻 > 窝轮新闻", "http://www.cnfol.hk/warrants/"],
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
        # 详情页
        if 'hk/news/ganggujujiao' in response.url:
            for i in range(0, 2000, 5):
                t = time.time()
                url = f"http://shell.cnfol.com/article/hk_article.php?classid=4057&start={i}&end=5&pathurl=http://www.cnfol.hk/news/ganggujujiao/&_={int(round(t * 1000))}"
                response.meta['num'] += 1
                yield from over_page(url, response, page_num=response.meta['num'], callback=self.parse_hk)
                # yield scrapy.Request(url, callback=self.parse_hk, meta=response.meta)

        elif 'hk/news/gangguzx' in response.url:
            for i in range(0, 2000, 5):
                t = time.time()
                url = f"http://shell.cnfol.com/article/hk_article.php?classid=4058&start={i}&end=5&pathurl=http://www.cnfol.hk/news/gangguzx/&_={int(round(t * 1000))}"
                response.meta['num'] += 1
                yield from over_page(url, response, page_num=response.meta['num'], callback=self.parse_hk)
                # yield scrapy.Request(url, callback=self.parse_hk, meta=response.meta)
                
        elif 'hk/news/dahangtuijian' in response.url:
            for i in range(0, 2000, 5):
                t = time.time()
                url = f"http://shell.cnfol.com/article/hk_article.php?classid=4062&start={i}&end=5&pathurl=http://www.cnfol.hk/news/dahangtuijian/&_={int(round(t * 1000))}"
                response.meta['num'] += 1
                yield from over_page(url, response, page_num=response.meta['num'], callback=self.parse_hk)
                # yield scrapy.Request(url, callback=self.parse_hk, meta=response.meta)
        
        elif 'hk/news/gncaijing/' in response.url:
            for i in range(0, 2000, 5):
                t = time.time()
                url = f"http://shell.cnfol.com/article/hk_article.php?classid=4072&start={i}&end=5&pathurl=http://www.cnfol.hk/news/gncaijing/&_={int(round(t * 1000))}"
                response.meta['num'] += 1
                yield from over_page(url, response, page_num=response.meta['num'], callback=self.parse_hk)
                # yield scrapy.Request(url, callback=self.parse_hk, meta=response.meta)
                
        elif 'cnfol.hk/ipo/' in response.url:
            for i in range(0, 2000, 5):
                t = time.time()
                url = f"http://shell.cnfol.com/article/hk_article.php?classid=4080&start={i}&end=5&pathurl=http://www.cnfol.hk/ipo/&_={int(round(t * 1000))}"
                response.meta['num'] += 1
                yield from over_page(url, response, page_num=response.meta['num'], callback=self.parse_hk)
                # yield scrapy.Request(url, callback=self.parse_hk, meta=response.meta)
                
        elif 'cnfol.hk/shhkc/' in response.url:
            for i in range(0, 2000, 5):
                t = time.time()
                url = f"http://shell.cnfol.com/article/hk_article.php?classid=4071,4075,4076&start={i}&end=5&pathurl=http://www.cnfol.hk/shhkc/&_={int(round(t * 1000))}"
                response.meta['num'] += 1
                yield from over_page(url, response, page_num=response.meta['num'], callback=self.parse_hk)
                # yield scrapy.Request(url, callback=self.parse_hk, meta=response.meta)
                
        elif 'hk/news/gangguxuetang/' in response.url:
            for i in range(0, 2000, 5):
                t = time.time()
                url = f"http://shell.cnfol.com/article/hk_article.php?classid=4176&start={i}&end=5&pathurl=http://www.cnfol.hk/news/gangguxuetang/&_={int(round(t * 1000))}"
                response.meta['num'] += 1
                yield from over_page(url, response, page_num=response.meta['num'], callback=self.parse_hk)
                # yield scrapy.Request(url, callback=self.parse_hk, meta=response.meta)
                
        elif 'cnfol.hk/warrants/' in response.url:
            for i in range(0, 2000, 6):
                t = time.time()
                url = f"http://shell.cnfol.com/article/hk_article.php?classid=4077,4078,4079&start={i}&end=6&pathurl=http://www.cnfol.hk/warrants/&_={int(round(t * 1000))}"
                response.meta['num'] += 1
                yield from over_page(url, response, page_num=response.meta['num'], callback=self.parse_hk)
                # yield scrapy.Request(url, callback=self.parse_hk, meta=response.meta)

    # 首页 - 保险 - 行业公司
    def parse_hk(self, response):
        data=json.loads(response.text).get('content')
        for d in data:
            url=d.get('Url')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text', '//*[@class="newDetailText"]/text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//span[@class="Mr10"]/text()')  # 来源/article_source
        item.add_xpath('author', '//p[@class="Fl"]/span[3]/text()', re='作者：(.*)')  # 作者/author
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

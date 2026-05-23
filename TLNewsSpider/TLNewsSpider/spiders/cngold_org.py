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



class CngoldOrgSpider(scrapy.Spider):
    name = 'cngold.org'
    # allowed_domains = ['cngold.org']
    site_name = '金投网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 期货首页 > 期货新闻", "https://futures.cngold.org/qsyw/list_602_all.html"],
        ["行业舆情", "首页 > 股票首页 > 股票新闻", "https://stock.cngold.org/news/list_2547_all.html"],
        ["行业舆情", "首页 > 财经首页 > 财经资讯", "https://finance.cngold.org/zixun/list_4026_all.html"],
        ["行业舆情", "首页 > 外汇首页 > 汇市时讯", "https://forex.cngold.org/hssx/list_359_all.html"],
        ["行业舆情", "首页 > 原油首页 > 热点资讯", "https://energy.cngold.org/news/list_422_all.html"]
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
        url_list=response.xpath('//*[@class="history_news_content"]/ul/li/a/@href').getall()
        for url in url_list:
            response.meta['num'] += 1
            yield from over_page(url, response, callback=self.parse_cngold,
                                 page_num=response.meta['num'])

    def parse_cngold(self, response):
        for url in response.css("ul.news_list li a"):
            response.meta['content_list']= []
            yield response.follow(url, callback=self.parse_content, meta=response.meta)

        # 翻页
        for index, page in enumerate(response.css('.show_info_page a')):
            yield from over_page(page, response, page_num=index)

    # 首页 - 保险 - 行业公司
    def parse_content(self, response):
        next_url=response.xpath('//a[text()="下一页"]/@href').get()
        content_rules = ContentRules()
        if next_url == None:
            # content_ = content_rules.extract(response.text)
            content_next = content_rules.extract(response.text)
            response.meta['content_list'].append(content_next)
            yield from self.parse_detail(response)
        else:
            # content_ = response.xpath('//*[@class="article_con"]//p//text()').getall()
            content_next = content_rules.extract(response.text)
            response.meta['content_list'].append(content_next)
            yield scrapy.Request(url=next_url,callback=self.parse_content,meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text),re='(.*)-')  # 标题/title
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text',response.meta['content_list'])
        # 自定义规则
        item.add_css('article_source', '.source .ly a:first-child::text')  # 来源/article_source
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

        # 上面获取值可能为空, 追加匹配值
        # item.add_xpath('title', '//h1/text() || //p/h5/text()', re='[标题]{2}:(.*?)')  # 标题/title
        # item.add_css('publish_date', 'p:nth-last-child(-n+5)', re="[0-9]{0,4}年[0-9]{1,2}月[0-9]{1,2}日")  # 发布日期/publish_date
        yield item.load_item()

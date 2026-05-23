# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time

from ..utils import date
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class AwebComCnSpider(scrapy.Spider):
    name = 'aweb.com.cn'
    allowed_domains = ['aweb.com.cn']
    site_name = '农博网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "农博首页>要闻频道>国内", "http://news.aweb.com.cn/china/"],
        ["行业舆情", "农博首页>要闻频道>国内>部委动态", "http://news.aweb.com.cn/china/bwdt/"],
        ["行业舆情", "农博首页>要闻频道>国内>行业新闻", "http://news.aweb.com.cn/china/hyxw/"],
        ["行业舆情", "农博首页>要闻频道>国内>农业院校", "http://news.aweb.com.cn/china/edu/"],
        ["企业舆情", "农博首页 > 财经频道 > 公司", "http://finance.aweb.com.cn/company/"]
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
        if 'news.aweb.com.cn/china/' in response.url:
            yield from self.parse_news(response)

        if 'finance.aweb.com.cn' in response.url:
            yield from self.parse_finance(response)

    # 首页>基金
    def parse_news(self, response):
        for url in response.css("a.newsgray"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)


    # 首页 - 保险 - 行业公司
    def parse_finance(self, response):
        for url in response.css("li a.a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        content=response.xpath('//*[@class="conT f14px"]//p//text()|//*[@class="conT f14px"]/span//text()|//*[@class="conT f14px"]/text()|//*[@class="conT f14px"]/div[not(@class)]//text()').getall()
        if content == []:
            content_=response.xpath('//*[@class="newList f_left"]/span//text()|//*[@class="newList f_left"]//p//text()').getall()
            content_text = [x.strip() for x in content_ if x.strip() != '']
            item.add_value('content_text', content_text)  # 正文内容/text_content
        else:
            content_text = [x.strip() for x in content if x.strip() != '']
            item.add_value('content_text', content_text)  # 正文内容/text_content
        
        # 自定义规则
        item.add_value('article_source', content_text,re='来源：(.*)[)]')  # 来源/article_source
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

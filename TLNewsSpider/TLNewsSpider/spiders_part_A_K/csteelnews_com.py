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



class CsteelnewsComSpider(scrapy.Spider):
    name = 'csteelnews.com'
    allowed_domains = ['csteelnews.com']
    site_name = '中国钢铁新闻网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 新闻中心 > 行业动态", "http://www.csteelnews.com/xwzx/hydt/"],
        ["企业舆情", "首页 > 新闻中心 > 上市公司资讯", "http://www.csteelnews.com/xwzx/ssgszx/"],
        ["宏观舆情", "首页>新闻中心>宏观经济", "http://www.csteelnews.com/xwzx/hgjj/"],
        ["行业舆情", "首页>新闻中心>国际钢铁", "http://www.csteelnews.com/xwzx/gjgt/"],
        ["行业舆情", "首页>新闻中心>原料耐材", "http://www.csteelnews.com/xwzx/ylnc/"],
        ["行业舆情", "首页>新闻中心>冶建钢构", "http://www.csteelnews.com/xwzx/yjgg/"],
        ["行业舆情", "首页>新闻中心>安全环保", "http://www.csteelnews.com/xwzx/aqhb/"],
        ["行业舆情", "首页>新闻中心>多元产业", "http://www.csteelnews.com/xwzx/dycy/"]
    ]
    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification,'url':url}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        yield from self.parse_csteelnews(response)
        for i in range(1,20):
            url=f"{response.meta['url']}index_{i}.html"
            yield from over_page(url, response, page_num=i, callback=self.parse_csteelnews)
            # yield response.follow(code, callback=self.parse_csteelnews, meta=response.meta)
        
    def parse_csteelnews(self,response):
        # 详情页:
        for url in response.css("li span.left a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title','//p[@class="title"]/text()')  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        content=response.xpath('//*[@class="TRS_Editor"]//div//text() | //*[@class="TRS_Editor"]//p//text()').getall()
        content_text=[x.strip() for x in content if x.strip() != '']
        item.add_value('content_text',content_text)  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="right"][1]/text()',re='来源：(.*)')  # 来源/article_source
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

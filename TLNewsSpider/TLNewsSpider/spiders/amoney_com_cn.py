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



class AmoneyComCnSpider(scrapy.Spider):
    name = 'amoney.com.cn'
    allowed_domains = ['amoney.com.cn']
    site_name = '第一理财网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 >信托", "http://www.amoney.com.cn/trust"],
        ["行业舆情", "首页 >基金", "http://www.amoney.com.cn/stock"],
        ["行业舆情", "首页 >房产", "http://www.amoney.com.cn/house"],
        ["行业舆情", "首页 >银行", "http://www.amoney.com.cn/bank"],
        ["行业舆情", "首页 >保险", "http://www.amoney.com.cn/insure"],
        ["行业舆情", "首页 >基金", "http://www.amoney.com.cn/fund"],
        ["行业舆情", "首页 >汽车", "http://www.amoney.com.cn/car"]
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
        yield from self.parse_amoney(response)


    # 首页>基金
    def parse_amoney(self, response):
        for url in response.css(".trust-read"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        page=response.xpath('//*[@rel="next"]/@href').get()
        response.meta['num'] +=1
        yield from over_page(page, response, page_num=response.meta['num'], callback=self.parse_amoney)


    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title', '//*[@class="content-nav"]/text()')  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text','//*[@class="hr-hot"]/p//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="content-title"]/span[2]/text()')  # 来源/article_source
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
        return item.load_item()

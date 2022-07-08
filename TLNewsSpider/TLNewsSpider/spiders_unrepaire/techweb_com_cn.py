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



class TechwebComCnSpider(scrapy.Spider):
    name = 'techweb.com.cn'
    allowed_domains = ['techweb.com.cn']
    site_name = 'IT精英'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["宏观舆情", "首页>新闻", "http://www.techweb.com.cn/roll/"],
        ["行业舆情", "首页 > 5G", "http://www.techweb.com.cn/new5g/"],
        ["行业舆情", "首页 > 芯片", "http://www.techweb.com.cn/microchips/"],
        ["行业舆情", "首页 > 云计算", "http://www.techweb.com.cn/newcloud/"],
        ["行业舆情", "首页 > AI", "http://www.techweb.com.cn/intelligent/"],
        ["行业舆情", "首页 > 科创板", "http://www.techweb.com.cn/newfinance/"],
        ["行业舆情", "首页 > 互联网", "http://www.techweb.com.cn/newinternet/"],
        ["行业舆情", "首页 > IT", "http://www.techweb.com.cn/newit/"],
        ["行业舆情", "首页 > 智能车", "http://www.techweb.com.cn/smartcar/"],
        ["行业舆情", "首页 > 手机数码", "http://www.techweb.com.cn/mobiledigital/"],
        ["行业舆情", "首页 > 游戏", "http://www.techweb.com.cn/newgame/"],
        ["行业舆情", "首页 > 区块链", "http://www.techweb.com.cn/newblockchain/"]
    ]

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if '/roll/' in response.url:
            yield from self.parse_roll(response)

        else:
            yield from self.parse_techweb(response)

    # 首页>基金
    def parse_roll(self, response):
        for url in response.css(".tit a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        for page in response.xpath('//a[text()=">"]'):
            yield response.follow(page, meta=response.meta)

    def parse_techweb(self, response):
        for url in response.css(".news_title h3 a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
        # 翻页
        for page in response.xpath('//a[text()="下一页"]'):
            yield response.follow(page, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        pd=self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('.','-')
        item.add_value('publish_date',publish_date )  # 发布日期/publish_date
        content=response.xpath('//*[@id="content"]/p//text()').getall()
        content_text=[x.strip() for x in content if x.strip() != '']
        item.add_value('content_text',content_text)  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="from"]/a/text()')  # 来源/article_source
        item.add_value('author',self.author_rules.extractor(response.text))  # 作者/author
        # 默认保存一般无需更改
        item.add_value('spider_time', date())  # 抓取时间
        item.add_value('created_time', date())  # 更新时间
        item.add_value('source_url', response.url)  # 详情网址/detail_url
        item.add_value('site_name', self.site_name)  # 站点名称
        item.add_value('site_url', urlsplit(response.url).netloc)  # 站点host
        item.add_value('classification', response.meta['classification'])  # 所属分类
        # 网页源码  调试阶段注释方便查看日志
        # item.add_value('html_text', response.text)  # 网页源码

        # 上面获取值可能为空, 追加匹配值
        # item.add_xpath('title', '//h1/text() || //p/h5/text()', re='[标题]{2}:(.*?)')  # 标题/title
        # item.add_css('publish_date', 'p:nth-last-child(-n+5)', re="[0-9]{0,4}年[0-9]{1,2}月[0-9]{1,2}日")  # 发布日期/publish_date
        return item.load_item()

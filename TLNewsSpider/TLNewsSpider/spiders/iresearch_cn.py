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



class IresearchCnSpider(scrapy.Spider):
    name = 'iresearch.cn'
    allowed_domains = ['iresearch.cn']
    site_name = '艾瑞网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 热点资讯 > 互联网", "https://news.iresearch.cn/include/pages/redis.aspx?rootId=1&classId=102&specialId=855"],
        ["企业舆情", "首页 > 热点资讯 > 移动互联网", "https://news.iresearch.cn/include/pages/redis.aspx?rootId=1&classId=101&specialId=855"],
        ["企业舆情", "首页 > 热点资讯 > 电子商务", "https://news.iresearch.cn/include/pages/redis.aspx?rootId=1&classId=103&specialId=855"],
        ["企业舆情", "首页 > 热点资讯 > 网络营销", "https://news.iresearch.cn/include/pages/redis.aspx?rootId=1&classId=104&specialId=855"],
        ["企业舆情", "首页 > 热点资讯 > 网络游戏", "https://news.iresearch.cn/include/pages/redis.aspx?rootId=1&classId=105&specialId=855"]
    ]

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification,'start_url':url}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        urls=response.xpath('//*[@class="txt"]/h3/a/@href').getall()
        for url in urls:
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        code_=re.split('/',url)
        code=re.findall('(\d*)',code_[-1])
        next_url=f"{response.meta['start_url']}&lastId=news.{code[0]}"
        yield response.follow(next_url, callback=self.parse, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="origin"]/span/text()',re='来源：(.*)作')  # 来源/article_source
        item.add_xpath('author','//*[@class="origin"]/span/text()',re='作者：(.*)')  # 作者/author
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

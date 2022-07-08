# -*- coding: utf-8 -*-

import re
import math
import scrapy
import json
from urllib.parse import urlsplit

from ..utils import date, over_page, date2time
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class JmLoupanComSpider(scrapy.Spider):
    name = 'jm.loupan.com'
    allowed_domains = ['jm.loupan.com']
    site_name = '楼盘网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["地区舆情", "首页>楼讯>热点楼讯", "https://jm.loupan.com/news/p-21.html"],
        ["地区舆情", "首页>楼讯>本地楼市", "https://jm.loupan.com/news/list-36.html"],
        ["地区舆情", "首页>楼讯>动态", "https://jm.loupan.com/dongtai/"]
    ]

    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            #若不需要用到num来传递次数，则可删去
            meta = {'classification': classification,'num':0}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页 无法限制时间
        for data in response.xpath('//*[@class="items"]'):
            data_url=data.xpath('.//*[@class="tit"]/a/@href').get()
            yield response.follow(data_url, callback=self.parse_detail, meta=response.meta)

        #
        # # 翻页
        page=response.xpath('//*[@class="pagenxt"]/@href').get()
        next_url=f"https://jm.loupan.com{page}"
        response.meta['num'] += 1
        yield from over_page(next_url, response, page_num=response.meta['num'], callback=self.parse)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text','//*[@class="content_text"]/p//text()')  # 正文内容/text_content
        item.add_xpath('content_text','//*[@class="content_text"]/section/section/section//text()')  # 正文内容/text_content
        item.add_xpath('content_text','//*[@class="article"]/p//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="infoBox"]/p[2]/text()',re='来源：\n (.*)')  # 来源/article_source
        item.add_xpath('article_source', '//*[@class="source"]/text()')  # 来源/article_source
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

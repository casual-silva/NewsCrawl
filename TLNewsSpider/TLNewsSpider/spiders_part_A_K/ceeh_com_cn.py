# -*- coding: utf-8 -*-

import re
import math
import scrapy
import json
from urllib.parse import urlsplit

from ..utils import date, over_page, date2time,pubdate_common
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class CeehComCnSpider(scrapy.Spider):
    name = 'ceeh.com.cn'
    allowed_domains = ['ceeh.com.cn']
    site_name = '全球经济导报网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["宏观舆情", "首页>财经", "http://www.ceeh.com.cn/finance/"],
        ["宏观舆情", "首页 >产经", "http://www.ceeh.com.cn/chanjing/"],
        ["宏观舆情", "首页 >金融", "http://www.ceeh.com.cn/jinrong/"],
        ["行业舆情", "首页 >股市", "http://www.ceeh.com.cn/gushi/"],
        ["行业舆情", "首页 >房产", "http://www.ceeh.com.cn/house/"],
        ["宏观舆情", "首页 >公司", "http://www.ceeh.com.cn/company/"]
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
        # 详情页
        for url in response.css(".level-list h2 a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        page=response.xpath('//a[text()="下一页"]/@href').get()
        date_list=response.xpath('//*[@class="import"]/span/text()').getall()
        pagetime=pubdate_common.handle_pubdate(date_list[-1],need_detail_time=True)
        page_time=date2time(time_str=pagetime)
        next_url=f"http://www.ceeh.com.cn{page}"
        response.meta['num'] += 1
        yield from over_page(next_url, response, page_time=page_time, page_num=response.meta['num'], callback=self.parse)
        #
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text', '//*[@class="article-content"]/p[not(@class)]//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="atime"]/text()',re='来源：(.*)')  # 来源/article_source
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

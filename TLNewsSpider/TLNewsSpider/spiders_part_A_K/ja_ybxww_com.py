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



class JaYbxwwComSpider(scrapy.Spider):
    name = 'ja.ybxww.com'
    allowed_domains = ['ja.ybxww.com']
    site_name = '江安新闻网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["地区舆情", "首页>要闻", "http://ja.ybxww.com/jayw.html"]
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
        for data in response.xpath('//*[@class="relate-news-wap2 "]/li/p'):
            data_url=data.xpath('./a/@href').get()
            data_time=data.xpath('./span/text()').get()
            url=f"http://ja.ybxww.com{data_url}"
            dt=pubdate_common.handle_pubdate(pubdate_str=data_time)
            pagetime=date2time(date_str=dt.strip())
            yield from over_page(url,response,page_num=1,page_time=pagetime,callback=self.parse_detail)

        # 翻页
        page=response.xpath('//a[text()="下一页"]/@href').get()
        next_url=f"http://ja.ybxww.com/{page}"
        response.meta['num'] += 1
        yield from over_page(next_url, response, page_time=pagetime, page_num=response.meta['num'], callback=self.parse)


    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="h-info"]/span[last()]/text()',re='来源：(.*)')  # 来源/article_source
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

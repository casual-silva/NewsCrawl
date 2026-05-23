# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time

from ..utils import date, over_page,date2time
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class CansiOrgCnSpider(scrapy.Spider):
    name = 'cansi.org.cn'
    allowed_domains = ['cansi.org.cn']
    site_name = '中国船舶工业行业协会'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 信息服务 > 统计服务", "http://www.cansi.org.cn/cms/document/show/43.html"],
        ["行业舆情", "首页>新闻中心>行业风采", "http://www.cansi.org.cn/cms/document/show/32.html"]
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
        for data in response.xpath('//li[@class="item"]'):
            data_url=data.xpath('./a/@href').get()
            data_time=data.xpath('.//span[@class="date"]/text()').get()
            url=f"http://www.cansi.org.cn{data_url}"
            data_time_=data_time.replace('[','').replace(']','')
            pagetime=date2time(date_str=data_time_)
            yield from over_page(url,response,page_time=pagetime,callback=self.parse_detail)

        # 翻页
        page=response.xpath('//*[text()="»"]/@href').get()
        next_url=f"http://www.cansi.org.cn/{page}"
        yield from over_page(next_url, response, page_time=pagetime, callback=self.parse)


    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        content=response.xpath('//*[@class="editbox"]/p/img/@src|//*[@class="editbox"]//text()').getall()
        content_text=[x.strip() for x in content if x.strip() != '']
        item.add_value('content_text',content_text)  # 正文内容/text_content
        # 自定义规则
        item.add_value('article_source', content_text, re='来源：(.*)）')
        item.add_value('article_source', content_text, re='来源于(.*)。')
        item.add_value('article_source', content_text, re='来自：(.*)）')
        item.add_value('article_source', content_text, re='编自(.*)）')
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

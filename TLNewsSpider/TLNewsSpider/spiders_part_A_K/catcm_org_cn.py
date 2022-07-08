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



class CatcmOrgCnSpider(scrapy.Spider):
    name = 'catcm.org.cn'
    allowed_domains = ['catcm.org.cn']
    site_name = '中国中药协会'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 行业资讯", "http://www.catcm.org.cn/newsdirectory.asp?cid=9&cname=%D0%D0%D2%B5%D7%CA%D1%B6"]
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
        
        for i in range(1,100):
            url='http://www.catcm.org.cn/newsdirectory.asp'
            data={'me_page': str(i),'cname': '%D0%D0%D2%B5%D7%CA%D1%B6','cid':'9' }
            yield from over_page(url, response, callback=self.parse_catcm, formdata=data,
                                 page_num=i)

    # 首页>基金
    def parse_catcm(self, response):
        for list in response.xpath('//ul[@class="tp"]/li'):
            url=list.xpath('./a/@href').get()
            pd=list.xpath('./span/text()').get()
            response.meta['pd']=pd.replace('\n', '').replace('\r', '').replace('\t', '')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title','//*[@id="xinwen_middle"]/h1/text()')  # 标题/title
        item.add_value('publish_date',response.meta['pd'])  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_value('article_source', content_rules.extract(response.text), re='（来源：(.*)）')
        item.add_value('article_source', content_rules.extract(response.text),re='来源：(.*)')  # 来源/article_source
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

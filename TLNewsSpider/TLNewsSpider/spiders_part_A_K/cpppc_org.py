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



class CpppcOrgSpider(scrapy.Spider):
    name = 'cpppc.org'
    allowed_domains = ['cpppc.org']
    site_name = '财政部政府和社会资本合作中心'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页>新闻动态>行业动态", "http://www.cpppc.org/xydt.jhtml"]
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
        for i in range(1,3):
            url=f"http://www.cpppc.org/content/page?channelIds=3500&orderBy=27&page={i}&size=20"
            yield scrapy.Request(url,callback=self.parse_jijing,meta=response.meta)
            
    def parse_jijing(self, response):
        data=json.loads(response.text).get('data')
        content=data.get('content')
        for con in content:
            source=con.get('source')
            sourceName=source.get('sourceName')
            response.meta['article_source']=sourceName
            url=con.get('url')
            detail_url=f"http://www.cpppc.org{url}"
            releaseTime=con.get('releaseTime')
            response.meta['publish_date']=releaseTime
            pagetime=date2time(time_str=releaseTime)
            yield from over_page(detail_url,response,page_num=1,page_time=pagetime,callback=self.parse_detail)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title', '//*[@class="common-card detail-card"]/h1/text()')  # 标题/title
        item.add_value('publish_date', response.meta['publish_date'])  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_value('article_source',response.meta['article_source'])  # 来源/article_source
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

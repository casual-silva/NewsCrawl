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



class PortcontainerComSpider(scrapy.Spider):
    name = 'portcontainer.com'
    allowed_domains = ['portcontainer.com']
    site_name = '中国港口集装箱网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 集箱信息", "http://www.portcontainer.com/newsMoreAction.do?command=query&jspName=/viewnewsmore.jsp&rootCategoryId=8a9289fb300b172d01300b1cfddf0001&moreId=8a9289fb300b172d01300b1cfddf0001"]
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
        url = 'http://www.portcontainer.com/newsMoreAction.do'
        for i in range(1,11):
            data = {'command': 'switchPages', 'jspName': '/viewnewsmore.jsp', 'dataIndex': '0', 'pageDirection': '4',
                    'deleteIndexs': '', 'queryType': '2', 'queryString': 'getNewsByCategory', 'pageIndex': str(i)}
            yield from over_page(url,response,callback=self.parse_next,formdata=data,page_num=i)
        
    def parse_next(self,response):
        for url in response.css(".news td a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title', '//*[@class="news_title"]/text()[3]')  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text','//*[@class="nei"]//p//text()')  # 正文内容/text_content
        # 自定义规则
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

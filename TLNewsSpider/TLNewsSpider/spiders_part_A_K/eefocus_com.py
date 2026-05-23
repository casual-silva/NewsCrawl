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



class EefocusComSpider(scrapy.Spider):
    name = 'eefocus.com'
    allowed_domains = ['eefocus.com']
    site_name = '与非网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "主页 > 行业热点", "https://www.eefocus.com/e/"],
        ["行业舆情", "首页>产业分析>更多", "https://www.eefocus.com/original/"],
        ["企业舆情", "首页 > 消费电子", "https://www.eefocus.com/consumer-electronics/"]
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
        #直接在parse里遍历页码的翻页
        if 'eefocus.com/e/' in  response.url:
           for i in range(1,51):
               url=f"https://www.eefocus.com/article/index/more.articles?p={i}&channel=&category=7"
               yield from over_page(url,response,page_num=i,callback=self.parse_jijing)
        
        elif 'eefocus.com/original/' in  response.url:
               yield from self.parse_baoxian(response)
            
        elif 'eefocus.com/consumer-electronics/' in  response.url:
           for i in range(1,31):
               url=f"https://www.eefocus.com/article/index/more.articles?p={i}&channel=13&category=-1"
               yield from over_page(url,response,page_num=i,callback=self.parse_jijing)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        data=json.loads(response.text).get('data')
        for d in data:
            url=d.get('url')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
            
        
    # 遍历url翻页方式
    def parse_baoxian(self, response):
        for url in response.css(".col-sm-9 a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        #
        # 翻页
        page = response.xpath('//a[text()="›"]/@href').get()
        next_url = f"https://www.eefocus.com{page}"
        response.meta['num'] += 1
        yield from over_page(next_url, response, page_num=response.meta['num'],
                             callback=self.parse_baoxian)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text','//*[@class="article-body"]/p//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_css('article_source', '.source .ly a:first-child::text')  # 来源/article_source
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

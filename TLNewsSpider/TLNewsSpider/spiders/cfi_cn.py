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



class CfiCnSpider(scrapy.Spider):
    name = 'cfi.cn'
    # allowed_domains = ['cfi.cn']
    site_name = '中财网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 产经 > IT", "http://industry.cfi.cn/BCA0A4127A4128A4143.html"],
        ["企业舆情", "首页 > 股票 > 公司快递", "http://stock.cfi.cn/BCA0A4127A4346A4439.html"],
        ["行业舆情", "首页 > 产经 > 行业聚焦", "https://industry.cfi.cn/BCA0A4127A4128A4144.html"],
        ["行业舆情", "首页 > 产经 > 能源", "https://industry.cfi.cn/BCA0A4127A4128A4139.html"],
        ["行业舆情", "首页 > 产经 > 地产", "https://industry.cfi.cn/BCA0A4127A4128A4138.html"],
        ["行业舆情", "首页 > 股票 > 个股", "https://stock.cfi.cn/BCA0A4127A4346A4441.html"]
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
        # 详情页
        if 'industry.cfi.cn' in response.url:
            yield from self.parse_industry(response)

        if 'stock.cfi.cn' in response.url:
            response.meta['num']=0
            yield from self.parse_stock(response)

    # 首页>基金
    def parse_industry(self, response):
        for url in response.xpath('//*[@class="zidiv2"]/a'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        for script in response.xpath('//*[@class="zidiv2"]/script[position()>1]/text()').getall():
            code=re.findall('\d+',script)
            code_=''.join(code)
            code_url=f"https://industry.cfi.cn/p{code_}.html"
            yield response.follow(code_url, callback=self.parse_detail, meta=response.meta)


    # 首页 - 保险 - 行业公司
    def parse_stock(self, response):
        for url in response.xpath('//*[@class="xinwen"]/a'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
        # 翻页
        page=response.xpath('//*[@alt="下一页"]/../@href').get()
        next_url=f"https://stock.cfi.cn/{page}"
        response.meta['num'] +=1
        yield from over_page(next_url, response, page_num=response.meta['num'], callback=self.parse_stock)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        date_=self.publish_date_rules.extractor(response.text)
        publish_date=''.join(date_).replace('年','-').replace('月','-').replace('日','')
        item.add_value('publish_date', publish_date)  # 发布日期/publish_date
        text=response.xpath('//*[@id="tdcontent"]/text()').getall()
        content_text=''.join(text).replace('\r','').replace('\n','')
        item.add_value('content_text', content_text)
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

        # 上面获取值可能为空, 追加匹配值
        # item.add_xpath('title', '//h1/text() || //p/h5/text()', re='[标题]{2}:(.*?)')  # 标题/title
        # item.add_css('publish_date', 'p:nth-last-child(-n+5)', re="[0-9]{0,4}年[0-9]{1,2}月[0-9]{1,2}日")  # 发布日期/publish_date
        return item.load_item()

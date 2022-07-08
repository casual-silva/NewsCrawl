# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit

from ..utils import date, over_page, date2time
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class A96369NetSpider(scrapy.Spider):
    name = '96369.net'
    allowed_domains = ['96369.net']
    site_name = '西本信干线'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页>行情分析>每日分析", "http://www.96369.net/news/list/15/9"],
        ["行业舆情", "首页>行情分析>库存观市", "http://www.96369.net/news/list/15/11"],
        ["行业舆情", "首页>行情分析>观点争鸣", "http://www.96369.net/news/list/15/12"],
        ["行业舆情", "首页>行情分析>钢市日记", "http://www.96369.net/news/list/15/10"],
        ["行业舆情", "首页>行情分析>炉料点评", "http://www.96369.net/news/list/15/18"],
        ["行业舆情", "首页>行情分析>期货分析", "http://www.96369.net/news/list/15/45"],
        ["行业舆情", "首页>产经数据>宏观数据", "http://www.96369.net/news/list/14/35"],
        ["行业舆情", "首页>产经数据>期货数据", "http://www.96369.net/news/list/14/25"],
        ["行业舆情", "首页>产经数据>下游数据", "http://www.96369.net/news/list/14/26"],
        ["行业舆情", "首页>产经数据>调价信息", "http://www.96369.net/news/list/14/13"],
        ["行业舆情", "首页>产经数据>行业数据", "http://www.96369.net/news/list/14/36"],
        ["行业舆情", "首页>产经数据>检修数据", "http://www.96369.net/news/list/14/14"],
        ["行业舆情", "首页>产经数据>上游数据", "http://www.96369.net/news/list/14/27"],
        ["行业舆情", "首页>产经数据>政策法规", "http://www.96369.net/news/list/14/64"],
        ["行业舆情", "首页>行业分析>每日分析", "http://www.96369.net/news/list/15/9"],
        ["行业舆情", "首页>行业分析>库存观市", "http://www.96369.net/news/list/15/11"],
        ["行业舆情", "首页>行业分析>观点争鸣", "http://www.96369.net/news/list/15/12"],
        ["行业舆情", "首页>行业分析>钢市日记", "http://www.96369.net/news/list/15/10"],
        ["行业舆情", "首页>行业分析>炉料点评", "http://www.96369.net/news/list/15/18"],
        ["行业舆情", "首页>行业分析>期货分析", "http://www.96369.net/news/list/15/45"],
        
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
        yield from self.parse_news(response)

    # 下一页的翻页方式
    def parse_news(self, response):
        for url in response.css(".warmlist p a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        page=response.xpath('//a[text()="下一页"]/@href').get()
        date_list=response.xpath('//*[@class="warmlist"]/p/em/text()').getall()
        page_time = date2time(date_str=date_list[-1])
        next_url=f"http://www.96369.net{page}"
        response.meta['num'] += 1
        yield from over_page(next_url, response, page_time=page_time,page_num=response.meta['num'], callback=self.parse)


    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        pd=self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('年','-').replace('月','-').replace('日',' ')
        item.add_value('publish_date',publish_date )  # 发布日期/publish_date
        item.add_xpath('content_text','//*[@class="cont-msg"]/p//text()' )  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="wll-new-detail"]/h6/text()',re='来源：(.*)')  # 来源/article_source
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

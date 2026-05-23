# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time

from ..utils import date,over_page
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class A10jqkaComCnSpider(scrapy.Spider):
    name = '10jqka.com.cn'
    allowed_domains = ['news.10jqka.com.cn','stock.10jqka.com.cn']
    site_name = '同花顺财经'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()
    # REDIRECT_ENABLED = False

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页>财经>财经要闻", "http://news.10jqka.com.cn/today_list/"],
        ["宏观舆情", "首页>财经>宏观经济", "http://news.10jqka.com.cn/cjzx_list/"],
        ["行业舆情", "首页>财经>产经新闻", "http://news.10jqka.com.cn/cjkx_list/"],
        ["企业舆情", "首页>财经>公司新闻", "http://news.10jqka.com.cn/fssgsxw_list/"],
        ["行业舆情", "首页>股票>行业研究", "http://stock.10jqka.com.cn/bkfy_list/"],
        ["企业舆情", "首页 >股票 > 港股 > 港股公司新闻", "http://stock.10jqka.com.cn/hks/ggdt_list/"]
    ]
    
    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification,'num':0,'dont_redirect': True}
            yield scrapy.Request(url, callback=self.parse, meta=meta,)

    def parse(self, response):
        yield from self.parse_jqka(response)
        # 详情页
    
    def parse_jqka(self,response):
        for url in response.css(".arc-title a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        response.meta['num'] += 1
        page=response.xpath('//a[@class="next"]/@href').get()
        yield from over_page(page, response, page_num=response.meta['num'], callback=self.parse)
        # page = response.xpath('//a[@class="next"]/@href').get()
        # yield scrapy.Request(page,callback=self.parse,meta=response.meta)
        #


    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        pd=self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('年','-').replace('月','-').replace('日','').replace('/','-')
        item.add_value('publish_date', publish_date)  # 发布日期/publish_date
        content=response.xpath('//*[@class="main-text atc-content"]//p/text()').getall()
        if content==[]:
            item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        else:
            content_text=[x.strip() for x in content if x.strip() != '']
            item.add_value('content_text',content_text)  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@id="source_baidu"]/a/text()')  # 来源/article_source
        item.add_value('author',self.author_rules.extractor(response.text))  # 作者/author
        # 默认保存一般无需更改
        item.add_value('spider_time', date())  # 抓取时间
        item.add_value('created_time', date())  # 更新时间
        item.add_value('source_url', response.url)  # 详情网址/detail_url
        item.add_value('site_name', self.site_name)  # 站点名称
        item.add_value('site_url', urlsplit(response.url).netloc)  # 站点host
        item.add_value('classification', response.meta['classification'])  # 所属分类
        # 网页源码  调试阶段注释方便查看日志
        # item.add_value('html_text', response.text)  # 网页源码

        # 上面获取值可能为空, 追加匹配值
        # item.add_xpath('title', '//h1/text() || //p/h5/text()', re='[标题]{2}:(.*?)')  # 标题/title
        # item.add_css('publish_date', 'p:nth-last-child(-n+5)', re="[0-9]{0,4}年[0-9]{1,2}月[0-9]{1,2}日")  # 发布日期/publish_date
        return item.load_item()

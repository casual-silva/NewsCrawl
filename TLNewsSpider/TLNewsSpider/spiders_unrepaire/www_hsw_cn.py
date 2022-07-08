# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit

from ..utils import date
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class WwwHswCnSpider(scrapy.Spider):
    name = 'www.hsw.cn'
    # allowed_domains = ['www.hsw.cn']
    site_name = '华商网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [

        ["宏观舆情", "首页>新闻>新闻首页", "http://news.hsw.cn/"],
        ["宏观舆情", "首页>财经>宏观", "http://finance.hsw.cn/hgjj/?rand=hYWECvBA"],
        ["宏观舆情", "首页>财经>产业经济", "http://finance.hsw.cn/cyjj/?rand=qBhUIXz0"]
    ]

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'rand' in response.url:
            yield from self.parse_hg(response)
        #
        elif 'http://news.hsw.cn/' in response.url:
            yield from self.parse_xwsy(response)
        elif 'cyjj' in response.url:
            yield from self.parse_hg(response)

    # 首页>新闻>新闻首页
    def parse_xwsy(self, response):
        for url in response.css(".hero ul .cf a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        # for page in response.css('#Page a::attr(href),.pageControl a::attr(href)'):
        #     yield response.follow(page, meta=response.meta)


    def parse_hg(self, response):
        for url in response.css(".mainlist .listleft ul li h3 a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        # for page in response.css('.mainlist .listleft .page .a1:last-child::attr(href)'):
        for page in response.css('.page a:nth-child(n+4)::attr(href)'):
            yield response.follow(page,meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_css('article_source', '#artibody::text,#source_baidu::text')  # 来源/article_source
        item.add_css('author', '#artibody .fr span::text,#editor_baidu::text')  # 作者/author

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

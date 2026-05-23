# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time

from ..utils import date
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class HuxiuComSpider(scrapy.Spider):
    name = 'huxiu.com'
    allowed_domains = ['huxiu.com']
    site_name = '虎嗅网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页>资讯>频道>车与出行", "https://www.huxiu.com/channel/21.html"],
        ["行业舆情", "首页>资讯>频道>医疗健康", "https://www.huxiu.com/channel/111.html"],
        ["行业舆情", "首页>资讯>频道>金融地产", "https://www.huxiu.com/channel/102.html"],
        ["行业舆情", "首页>资讯>频道>财经", "https://www.huxiu.com/channel/115.html"]
    ]

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'huxiu.com/channel/21.html' in response.url:
            yield from self.parse_21(response)

        elif '/channel/111.html' in response.url:
            yield from self.parse_111(response)
            
        elif '/channel/102.html' in response.url:
            yield from self.parse_102(response)
            
        elif 'channel/115.html' in response.url:
            yield from self.parse_115(response)

    # 首页>基金
    def parse_21(self, response):
        for url in response.xpath('//div[@class="article-item article-item--normal"]/a'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
            
        url_='https://article-api.huxiu.com/web/channel/articleList'
        #异步加载的post请求所带的参数
        id='21'
        response.meta['id']=id
        body={'platform':'www','last_time':'1640067927','channel_id':id}
        yield scrapy.FormRequest(url_,callback=self.parse_articleList,meta=response.meta,formdata=body)

    def parse_111(self, response):
        for url in response.xpath('//div[@class="article-item article-item--normal"]/a'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
        url_ = 'https://article-api.huxiu.com/web/channel/articleList'
        # 异步加载的post请求所带的参数
        id='111'
        response.meta['id'] = id
        body = {'platform': 'www', 'last_time': '1640259831', 'channel_id': id}
        yield scrapy.FormRequest(url_, callback=self.parse_articleList, meta=response.meta, formdata=body)

    def parse_102(self, response):
        for url in response.xpath('//div[@class="article-item article-item--normal"]/a'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
        url_ = 'https://article-api.huxiu.com/web/channel/articleList'
        # 异步加载的post请求所带的参数
        id='102'
        response.meta['id'] = id
        body = {'platform': 'www', 'last_time': '1640075823', 'channel_id': id}
        yield scrapy.FormRequest(url_, callback=self.parse_articleList, meta=response.meta, formdata=body)

    def parse_115(self, response):
        for url in response.xpath('//div[@class="article-item article-item--normal"]/a'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
        url_ = 'https://article-api.huxiu.com/web/channel/articleList'
        # 异步加载的post请求所带的参数
        id='115'
        response.meta['id'] = id
        body = {'platform': 'www', 'last_time': '1640148958', 'channel_id': id}
        yield scrapy.FormRequest(url_, callback=self.parse_articleList, meta=response.meta, formdata=body)

    # 首页 - 保险 - 行业公司
    def parse_articleList(self, response):
        id=response.meta['id']
        data=json.loads(response.text).get('data')
        datalist = data.get('datalist')
        for d in datalist:
            url=d.get('share_url')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        last_time=''.join(data.get('last_time'))
        if last_time != None:
            body={'platform':'www','last_time':last_time,'channel_id':id}
            yield scrapy.FormRequest(response.url,callback=self.parse_articleList,meta=response.meta,formdata=body)
        #

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title','//h1[@class="article__title"]/text()')
        item.add_xpath('title', '//div[@id="article"]/div[@class="title"]/text()')  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
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
        # item.add_value('html_text', response.text)  # 网页源码

        # 上面获取值可能为空, 追加匹配值
        # item.add_xpath('title', '//h1/text() || //p/h5/text()', re='[标题]{2}:(.*?)')  # 标题/title
        # item.add_css('publish_date', 'p:nth-last-child(-n+5)', re="[0-9]{0,4}年[0-9]{1,2}月[0-9]{1,2}日")  # 发布日期/publish_date
        return item.load_item()

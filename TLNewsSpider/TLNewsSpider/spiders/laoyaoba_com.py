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



class LaoyaobaComSpider(scrapy.Spider):
    name = 'laoyaoba.com'
    allowed_domains = ['laoyaoba.com']
    site_name = '爱集微'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 概念股", "https://www.laoyaoba.com/list/117"]
    ]

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        for li in response.xpath('//*[@class="list-content"]/li'):
            data_id= li.xpath('./@data-id').get()
            url=li.xpath('./a/@href').get()
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
            
        next_url='https://www.laoyaoba.com/api/news/feedstream'
        data={'after_id': data_id,'category_id': '117','distinct_id': '17eed1d7698137c-0d548f8e80cec4-576153e-2073600-17eed1d7699cc9',
              'limit': '10','source': 'pc','token':''}
        yield scrapy.FormRequest(url=next_url, callback=self.parse_next, meta=response.meta,formdata=data)

    def parse_next(self, response):
        data=json.loads(response.text).get('data')
        for d in data:
            tag_list=d.get('tag_list')
            for tl in tag_list:
                news_id=tl.get('news_id')
                url=f"https://www.laoyaoba.com/n/{news_id}"
                yield scrapy.Request(url,callback=self.parse_detail, meta=response.meta)
        data = {'after_id': str(news_id), 'category_id': '117',
                'distinct_id': '17eed1d7698137c-0d548f8e80cec4-576153e-2073600-17eed1d7699cc9',
                'limit': '10', 'source': 'pc', 'token': ''}
        yield scrapy.FormRequest(url=response.url, callback=self.parse_next, meta=response.meta,formdata=data)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title','//*[@class="article"]/h1/text()')  # 标题/title
        pd=self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('/','-')
        item.add_value('publish_date', publish_date)  # 发布日期/publish_date
        item.add_xpath('content_text', '//article/p[not(@class)]//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="content-center-text-info-left"]/p[1]/text()',re='来源：(.*)')  # 来源/article_source
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

# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit

from ..utils import date
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor
import json
import time
import re

class SohuComSpider(scrapy.Spider):
    name = 'sohu.com'
    site_name = '搜狐'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 >  财经 >  公司深读",
         "http://mp.sohu.com/profile?xpt=c29odWNqeWMyMDE3QHNvaHUuY29t&_f=index_pagemp_1&spm=smpc.ch15.top-subnav.7.1628493152714vMgj4Sa"],
        ["宏观舆情", "首页 >  财经 >  宏观",
         "https://business.sohu.com/category/macrography?spm=smpc.ch15.top-subnav.2.1639038675760bMTnsKo"],
        ["行业舆情", "首页 >  财经 >  房地产",
         "https://business.sohu.com/category/realty?spm=smpc.ch15-fi.top-subnav.5.1639038788924Tc8pk6o"],
        ["企业舆情", "首页 >  财经 >  科创板",
         "https://business.sohu.com/category/kcb?spm=smpc.ch15-realty.top-subnav.9.1639393016853WlJ1xcp"]
    ]

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'mp.sohu.com/profile?' in response.url:
            for i in range(1,50):
                url=f"http://v2.sohu.com/author-page-api/author-articles/pc/100001551?pNo={i}&columnId=273916"
                yield scrapy.Request(url, callback=self.parse_mp, meta=response.meta)

        elif 'category/macrography?' in response.url:
            url = 'https://v2.sohu.com/integration-api/mix/region/6732?size=100&adapter=pc&secureScore=50&page=1'
            yield scrapy.Request(url, callback=self.parse_macrography, meta=response.meta)
        
        elif '/category/realty?s' in response.url:
            url = 'https://v2.sohu.com/integration-api/mix/region/6734?size=500&adapter=pc&secureScore=50&page=1'
            yield scrapy.Request(url, callback=self.parse_macrography, meta=response.meta)
            
        elif 'category/kcb?' in response.url:
            url = 'https://v2.sohu.com/integration-api/mix/region/8868?size=1000&adapter=pc&secureScore=50&page=1'
            yield scrapy.Request(url, callback=self.parse_macrography, meta=response.meta)

    def parse_mp(self, response):
        data=json.loads(response.text).get('data')
        for d in data.get('pcArticleVOS'):
            url=f"https://{d.get('link')}"
            yield scrapy.Request(url=url, callback=self.parse_detail,meta=response.meta)

    # 首页 - 保险 - 行业公司
    def parse_macrography(self, response):
        data=json.loads(response.text).get('data')
        for d in data:
            url_=d.get('url')
            url=f"https:{url_}"
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        # item.add_xpath('article_source', '//*[@class="article"]/p/strong[2]/text()',re='出品 |(.*)')  # 来源/article_source
        au=content_rules.extract(response.text)
        au_=''.join(re.findall('作者(.*)',au))
        au_=au_.replace('|','').replace(' ','').replace('｜','').replace('丨','')
        item.add_value('author', au_)  # 作者/author
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

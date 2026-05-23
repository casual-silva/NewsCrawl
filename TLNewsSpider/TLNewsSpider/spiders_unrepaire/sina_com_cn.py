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

class SinaComCnSpider(scrapy.Spider):
    name = 'sina.com.cn'
    # allowed_domains = ['sina.com.cn']
    site_name = '新浪网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "新浪财经 > 产经 > 公司新闻", "http://finance.sina.com.cn/chanjing/"],
        ["企业舆情", "首页 > 新股 > 双枪", "http://finance.sina.com.cn/stock/newstock/"],
        ["企业舆情", "首页 > 财经>港股 >  公司要闻", "http://finance.sina.com.cn/roll/index.d.html?cid=57038&page=1"],
        ["企业舆情", "首页 > A股新闻资讯", "https://t.cj.sina.com.cn/k/api/article/lists_by_column?sort_id=3"],
        ["企业舆情", "首页 > 基金新闻资讯", "https://t.cj.sina.com.cn/k/api/article/lists_by_column?sort_id=6"],
        ["企业舆情", "首页 > 黄金新闻资讯", "https://t.cj.sina.com.cn/k/api/article/lists_by_column?sort_id=9"],
        ["宏观舆情", "首页 > 期货新闻资讯", "https://t.cj.sina.com.cn/k/api/article/lists_by_column?sort_id=7"],
    ]

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        
        if 'chanjing' in response.url:
            for i in range(1,251):
                t=time.time()
                url=f"https://feed.mix.sina.com.cn/api/roll/get?pageid=164&lid=1694&num=10&page={i}&_={int(round(t * 1000))}"
                yield scrapy.Request(url,callback=self.parse_chanjing,meta=response.meta)

        elif 'stock/newstock/' in response.url:
            for i in range(1, 251):
                t = time.time()
                url = f"https://feed.mix.sina.com.cn/api/roll/get?pageid=205&lid=1789&num=10&page={i}&_={int(round(t * 1000))}"
                yield scrapy.Request(url, callback=self.parse_chanjing, meta=response.meta)
        
        elif 'roll/index.d.html' in response.url:
            # 页面和保险一样
            yield from self.parse_roll(response)
            
        elif 'cj.sina.com.cn' in response.url:
            for i in range(1, 251):
                t = time.time()
                url = f"{response.url}&page={i}&_={int(round(t * 1000))}"
                yield scrapy.Request(url, callback=self.parse_cj, meta=response.meta)
            

    def parse_chanjing(self, response):
        datas=json.loads(response.text).get('result')
        data=datas.get('data')
        for i in data:
            url=i.get('url')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        # 翻页
        for page in response.css('#Page a::attr(href),.pageControl a::attr(href)'):
            yield response.follow(page, meta=response.meta)

    # 首页 - 保险 - 行业公司
    def parse_roll(self, response):
        for url in response.xpath('//*[@class="listBlk"]/ul/li/a'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
        # 翻页
        for page in response.xpath('//span[@class="pagebox_next"]/a'):
            yield response.follow(page, meta=response.meta)

    def parse_cj(self, response):
        datas = json.loads(response.text).get('result')
        data = datas.get('data')
        list=data.get('lists')
        for i in list:
            url=i.get('url')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
           # 翻页
        
            
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        content=response.xpath('//*[@class="article"]/p//text()').getall()
        item.add_value('content_text', content)  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="source ent-source"]/text()')  # 来源/article_source
        item.add_css('author', '.source #author_baidu a::text')  # 作者/author
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

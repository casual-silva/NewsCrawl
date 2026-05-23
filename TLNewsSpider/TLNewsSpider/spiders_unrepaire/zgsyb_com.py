# -*- coding: utf-8 -*-
import json
import re
import math
import scrapy
from urllib.parse import urlsplit

from ..utils import date, over_page
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor
from lxml import etree


class ZgsybComSpider(scrapy.Spider):
    name = 'zgsyb.com'
    allowed_domains = ['zgsyb.com']
    site_name = '中国水运网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页>热闻", "http://www.zgsyb.com/column.html?cid=3009"]
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
        url='http://api.zgsyb.com/api/getSubColumns?&cid=3009&type=2'
        yield scrapy.Request(url,callback=self.parse_jijing,meta=response.meta)
        
    def parse_jijing(self, response):
        articles=json.loads(response.text).get('articles')
        for data in articles:
            fileID=data.get('fileID')
            url=f"http://api.zgsyb.com/api/getArticle?aid={fileID}"
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        
        for i in range(20,40000,20):
            response.meta['num'] +=1
            next_url=f"http://api.zgsyb.com/api/getArticles?cid=3009&lastFileID={fileID}&rowNumber={i}"
            yield from over_page(next_url,response,page_num=response.meta['num'],callback=self.parse_baoxian)

    def parse_baoxian(self, response):
        list=json.loads(response.text).get('list')
        for li in list:
            fileID = li.get('fileID')
            url = f"http://api.zgsyb.com/api/getArticle?aid={fileID}"
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
    def parse_detail(self, response):
        html=json.loads(response.text)
        title=html.get('title')
        publishTime=html.get('publishTime')
        content=html.get('content')
        text=etree.HTML(content)
        content_text=text.xpath('//text()')
        source=html.get('source')
        author=html.get('author')
        fileID=html.get('fileID')
        source_url=f"http://www.zgsyb.com/news.html?aid={fileID}"
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        item.add_value('title', title)  # 标题/title
        item.add_value('publish_date', publishTime)  # 发布日期/publish_date
        item.add_value('content_text', content_text)  # 正文内容/text_content
        item.add_value('article_source', source)  # 来源/article_source
        item.add_value('author',author)  # 作者/author
        # # 默认保存一般无需更改
        item.add_value('spider_time', date())  # 抓取时间
        item.add_value('created_time', date())  # 更新时间
        item.add_value('source_url', source_url)  # 详情网址/detail_url
        item.add_value('site_name', self.site_name)  # 站点名称
        item.add_value('site_url', urlsplit(response.url).netloc)  # 站点host
        item.add_value('classification', response.meta['classification'])  # 所属分类
        # 网页源码  调试阶段注释方便查看日志
        item.add_value('html_text', response.text)  # 网页源码
        return item.load_item()

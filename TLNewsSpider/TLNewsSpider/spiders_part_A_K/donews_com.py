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



class DonewsComSpider(scrapy.Spider):
    name = 'donews.com'
    allowed_domains = ['donews.com']
    site_name = 'DoNews'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页>快讯", "https://www.donews.com/newsflash/index"],
        ["企业舆情", "首页>游戏", "https://www.donews.com/ent/index"],
        ["企业舆情", "首页>3C", "https://www.donews.com/digital/index"],
        ["企业舆情", "首页>汽车", "https://www.donews.com/automobile/index"],
        ["企业舆情", "首页>娱乐", "https://www.donews.com/recreation/index"]
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
        if 'newsflash/index' in response.url:
            yield from self.parse_newsflash(response)

        elif 'ent/index' in response.url:
            for i in range(1,1000):
                url=f"https://www.donews.com/ent/more_ent_ajax?page={i}"
                yield from over_page(url, response, page_num=i, callback=self.parse_ano)
                # yield scrapy.Request(url,callback=self.parse_ano,meta=response.meta)
                
        elif 'digital/index' in response.url:
            for i in range(1,1000):
                url=f"https://www.donews.com/digital/more_ent_ajax?page={i}"
                yield from over_page(url, response, page_num=i, callback=self.parse_ano)
                # yield scrapy.Request(url,callback=self.parse_ano,meta=response.meta)
                
        elif 'automobile/index' in response.url:
            for i in range(1,1000):
                url=f"https://www.donews.com/automobile/ajax_news_more?page={i}"
                yield from over_page(url, response, page_num=i, callback=self.parse_ano)
                # yield scrapy.Request(url,callback=self.parse_ano,meta=response.meta)
                
        elif 'recreation/index' in response.url:
            for i in range(1,1000):
                url=f"https://www.donews.com/recreation/more_ent_ajax?page={i}"
                yield from over_page(url, response, page_num=i, callback=self.parse_ano)
                # yield scrapy.Request(url,callback=self.parse_ano,meta=response.meta)
            

    def parse_newsflash(self, response):
        urls=response.xpath('//*[@id="newloadmore"]/div/a/@href').getall()
        response.meta['author'] = 'None'
        for url in urls:
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        #下一页请求需要页面上最后一个文章url的code作为接口的id
        last_url=urls[-1]
        last_code=re.findall('8/(.*).html',last_url)
        code=''.join(last_code)
        next_url=f"https://www.donews.com/newsflash/more_news_ajax?id={code}"
        yield response.follow(next_url, callback=self.parse_next, meta=response.meta)

    # 首页 - 保险 - 行业公司
    def parse_next(self, response):
       for data in json.loads(response.text):
           id = data.get('id')
           url=data.get('url')
           response.meta['author'] = 'None'
           if url is None:
               print("url is None")
           else:
               yield response.follow(url, callback=self.parse_detail, meta=response.meta)
       next_url = f"https://www.donews.com/newsflash/more_news_ajax?id={id}"
       yield response.follow(next_url, callback=self.parse_next, meta=response.meta)
       
    def parse_ano(self,response):
        for data in json.loads(response.text):
            url = data.get('url')
            response.meta['author'] = data.get('author')
            if url is None:
                print("url is None")
            else:
                yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title','//*[@class="general-content-title"]/text()')  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text', '//*[@class="general-article"]/p/text()')  # 正文内容/text_content
        # 自定义规则
        item.add_css('article_source', '.source .ly a:first-child::text')  # 来源/article_source
        item.add_css('author','.source .ly a:first-child::text')
        item.add_value('author',response.meta['author'])  # 作者/author
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

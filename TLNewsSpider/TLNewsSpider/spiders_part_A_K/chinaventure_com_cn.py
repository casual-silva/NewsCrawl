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


class ChinaventureComCnSpider(scrapy.Spider):
    name = 'chinaventure.com.cn'
    allowed_domains = ['chinaventure.com.cn']
    site_name = '投资中国'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页＞5G", "https://www.chinaventure.com.cn/news/83.html"],
        ["行业舆情", "首页＞健康", "https://www.chinaventure.com.cn/news/111.html"],
        ["行业舆情", "首页＞教育", "https://www.chinaventure.com.cn/news/110.html"],
        ["行业舆情", "首页＞地产", "https://www.chinaventure.com.cn/news/112.html"],
        ["行业舆情", "首页＞金融", "https://www.chinaventure.com.cn/news/113.html"],
        ["行业舆情", "首页＞新消费", "https://www.chinaventure.com.cn/news/116.html"]
    ]
    
    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification,'num':0}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'news/83.html' in response.url:
            response.meta['channel_id']= '83'
            yield scrapy.Request(url=response.url, callback=self.parse_news, meta=response.meta,dont_filter=True)

        elif 'news/111.html' in response.url:
            response.meta['channel_id'] = '111'
            yield scrapy.Request(url=response.url, callback=self.parse_news, meta=response.meta, dont_filter=True)
            
        elif 'news/110.html' in response.url:
            response.meta['channel_id'] = '110'
            yield scrapy.Request(url=response.url, callback=self.parse_news, meta=response.meta, dont_filter=True)
            
        elif 'news/112.html' in response.url:
            response.meta['channel_id'] = '112'
            yield scrapy.Request(url=response.url, callback=self.parse_news, meta=response.meta, dont_filter=True)
            
        elif 'news/113.html' in response.url:
            response.meta['channel_id'] = '113'
            yield scrapy.Request(url=response.url, callback=self.parse_news, meta=response.meta, dont_filter=True)
            
        elif 'news/116.html' in response.url:
            response.meta['channel_id'] = '116'
            yield scrapy.Request(url=response.url, callback=self.parse_news, meta=response.meta, dont_filter=True)

    # 首页>基金
    def parse_news(self, response):
        for url in response.xpath('//ul[@class="common_newslist_pc"]/li/a/@href'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        next_url = 'https://rsdata.chinaventure.com.cn/api/getNewsListByChannel'
        for  i in range(21,1000,60):
            response.meta['num'] += 1
            data={'channel_id':response.meta['channel_id'],'begin_num':str(i),'size':'60','page':'1'}
            yield from over_page(next_url, response, callback=self.parse_next, formdata=data,
                                 page_num=response.meta['num'])
            # yield scrapy.FormRequest(next_url,callback=self.parse_next,meta=response.meta,formdata=data)

    # 首页 - 保险 - 行业公司
    def parse_next(self, response):
        for data in json.loads(response.text).get('data').get('channel_news_list'):
            url_=data.get('news_template_address')
            url_=''.join(url_)
            url=f"https://www.chinaventure.com.cn/{url_}"
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text', '//*[@class="article_slice_pc clearfix"]/p//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="source_author"]/span[1]/text()')  # 来源/article_source
        item.add_xpath('author','//*[@class="source_author"]/span[last()]/text()')  # 作者/author
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

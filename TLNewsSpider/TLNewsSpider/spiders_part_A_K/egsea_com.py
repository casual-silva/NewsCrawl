# -*- coding: utf-8 -*-

import re
import math
import scrapy
import json
from urllib.parse import urlsplit

from ..utils import date, over_page, date2time
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class EgseaComSpider(scrapy.Spider):
    name = 'egsea.com'
    allowed_domains = ['egsea.com']
    site_name = 'e公司'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页>基金分析", "https://fund.stockstar.com/list/1297.shtml"],
        ["企业舆情", "首页-保险-行业公司", "https://insurance.stockstar.com/list/5031.shtml"]
    ]
    headers={'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36',
             'x-requested-with':'XMLHttpRequest'
             }

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
        url=f"https://www.egsea.com/news/intelligence.html?page=1&pageTime=0&per-page=10"
        yield scrapy.Request(url,callback=self.parse_jijing,headers=self.headers,meta=response.meta)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        data=json.loads(response.text).get('data')
        for d in data:
            pageTime=d.get('pageTime')
            url=d.get('url')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        response.meta['num']+=1
        next_url=f"https://www.egsea.com/news/intelligence.html?page={response.meta['num']}&pageTime={pageTime}&per-page=10"
        page_time=int(pageTime)
        yield from over_page(next_url, response, page_time=page_time, page_num=response.meta['num'],
                             callback=self.parse_jijing,headers=self.headers)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text','//*[@class="article-content-detail"]/div[1]/p//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="source"]/text()',re='来源：(.*)')  # 来源/article_source
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

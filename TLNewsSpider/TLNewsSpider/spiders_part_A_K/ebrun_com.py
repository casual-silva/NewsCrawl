# -*- coding: utf-8 -*-

import re
import math
import scrapy
import json
from urllib.parse import urlsplit
from lxml import etree
from ..utils import date, over_page, date2time
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class EbrunComSpider(scrapy.Spider):
    name = 'ebrun.com'
    allowed_domains = ['ebrun.com']
    site_name = '亿邦动力网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页>产业互联网", "https://www.ebrun.com/information/industry/"],
        ["企业舆情", "首页>资讯", "https://www.ebrun.com/information/?eb=dszx_chan_nav"]
    ]

    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            #若不需要用到num来传递次数，则可删去
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta,dont_filter=True)

    def parse(self, response):
        # 详情页
        #直接在parse里遍历页码的翻页,/时间不排序不规律，无法用时间限制
        if 'information/industry/' in  response.url:
           for i in range(1,16):
               url=f"https://www.ebrun.com/information/industry/more/{i}?date=&exists_item_count=22"
               yield from over_page(url,response,page_num=i,callback=self.parse_jijing)
               
        elif 'information/?eb=dszx_chan_nav' in  response.url:
           for i in range(1,301):
               url=f"https://www.ebrun.com/information/more/{i}?date=&exists_item_count=20"
               yield from over_page(url,response,page_num=i-5,callback=self.parse_jijing)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        data=json.loads(response.text).get('data')
        html=data.get('html')
        text=etree.HTML(html)
        url_list=text.xpath('//*[@class="info"]//p[@class="title"]/a/@href')
        for url in url_list:
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text','//*[@class="post-text"]/p//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="source"]/p/span[2]/text()',re='文章来源：(.*)')  # 来源/article_source
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

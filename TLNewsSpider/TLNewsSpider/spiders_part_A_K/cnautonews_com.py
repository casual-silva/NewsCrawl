# -*- coding: utf-8 -*-

import re
import math
import time

import scrapy
import json
from urllib.parse import urlsplit

from ..utils import date, over_page, date2time
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class CnautonewsComSpider(scrapy.Spider):
    name = 'cnautonews.com'
    allowed_domains = ['cnautonews.com']
    site_name = '中国汽车报'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页>推荐>要闻", "http://www.cnautonews.com/yaowen/list_160_1.html"]
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
        for i in range(1,91):
            nowtime = int(time.time() - i * 86400)
            nowtime_ = date(nowtime)
            timelist = re.findall('(.*) ', nowtime_)
            timestr = ''.join(timelist)
            datetime = timestr.replace('-', '')
            url=f"http://www.cnautonews.com/js/160/mi4_sub_articles_{datetime}.js"
            yield from over_page(url,response,page_num=1,page_time=nowtime,callback=self.parse_jijing)
        

    # 下一页的翻页方式
    def parse_jijing(self, response):
        datalist=re.findall('var MI4_PAGE_ARTICLE = \[(.*)\]',response.text)
        for data in datalist:
            data_parse=json.loads(data)
            url=data_parse.get('url')
            miOrigin=data_parse.get('miOrigin')
            pubAuthor=data_parse.get('pubAuthor')
            miContentTxt=data_parse.get('miContentTxt')
            pub_date=data_parse.get('pub_date')
            title=data_parse.get('title')
            response.meta['article_source']=miOrigin
            response.meta['pubAuthor']=pubAuthor
            response.meta['miContentTxt']=miContentTxt
            response.meta['pub_date']=pub_date
            response.meta['title']=title
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        item.add_value('title', response.meta['title'])  # 标题/title
        item.add_value('publish_date', response.meta['pub_date'])  # 发布日期/publish_date
        item.add_value('content_text', response.meta['miContentTxt'])  # 正文内容/text_content
        # 自定义规则
        item.add_value('article_source',response.meta['article_source'])  # 来源/article_source
        item.add_value('author',response.meta['pubAuthor'])  # 作者/author
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

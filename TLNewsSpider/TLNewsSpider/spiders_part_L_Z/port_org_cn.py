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



class PortOrgCnSpider(scrapy.Spider):
    name = 'port.org.cn'
    allowed_domains = ['port.org.cn']
    site_name = '中国港口网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "中国港口 > 行业资讯 > 港航要闻", "http://www.port.org.cn/list/1003_1023_0.htm"],
        ["行业舆情", "中国港口 > 行业资讯 > 多式联运", "http://www.port.org.cn/list/1003_1025_0.htm"],
        ["行业舆情", "中国港口 > 行业资讯 > 内陆港", "http://www.port.org.cn/list/1003_1026_0.htm"],
        ["行业舆情", "中国港口 > 行业资讯 > 智慧绿色", "http://www.port.org.cn/list/1003_1027_0.htm"],
        ["行业舆情", "中国港口 > 行业资讯 > 综合物流", "http://www.port.org.cn/list/1003_1028_0.htm"]
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
        if '/list/1003_1023_0.htm' in response.url:
            for i in range(1,31):
                url=f"http://www.port.org.cn/list/1003_1023_{i}.htm"
                yield from over_page(url,response,page_num=i,callback=self.parse_jijing)
                
        elif '/list/1003_1025_0.htm' in response.url:
            for i in range(1,3):
                url=f"http://www.port.org.cn/list/1003_1025_{i}.htm"
                yield scrapy.Request(url,callback=self.parse_jijing,meta=response.meta)
                
        else:
            yield from self.parse_jijing(response)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        for url in response.css(".List_class ul li a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        pd=self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('/','-')
        item.add_value('publish_date',publish_date )  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="info_TitleUrl"]/text()',re='来源：(.*)')  # 来源/article_source
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

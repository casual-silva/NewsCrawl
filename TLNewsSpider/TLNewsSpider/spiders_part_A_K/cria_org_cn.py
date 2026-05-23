# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time

from ..utils import date, over_page,date2time
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class CriaOrgCnSpider(scrapy.Spider):
    name = 'cria.org.cn'
    allowed_domains = ['cria.org.cn']
    site_name = '中国橡胶网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "中国橡胶网 > 企业新闻", "http://www.cria.org.cn/newslist/6.html"],
        ["行业舆情", "中国橡胶网 > 行业新闻", "http://www.cria.org.cn/newslist/3.html"]
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
        for data in response.xpath('//*[@class="enterprise_news_c p_b20"]/ul/li'):
            data_url=data.xpath('./a/@href').get()
            data_time=data.xpath('./span/text()').get()
            url=f"http://www.cria.org.cn{data_url}"
            pagetime=date2time(date_str=data_time)
            yield from over_page(url,response,page_time=pagetime,callback=self.parse_detail)

        # 翻页
        page = response.xpath('//a[@class="st"]/@href').get()
        next_url = f"http://www.cria.org.cn{page}"
        yield from over_page(next_url, response, page_time=pagetime, callback=self.parse)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title', '//*[@class="enterprise_news_t"]/h1/text()')  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text', '//*[@class="news_details_c p20"]/p[not(@style)]//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="news_details_c p20"]/p[last()]/text()',re='来源：(.*)')  # 来源/article_source
        item.add_xpath('article_source', '//*[@class="enterprise_news_t"]/span[2]/text()', re='来源: (.*)')
        item.add_xpath('author','//*[@class="enterprise_news_t"]/span[3]/text()',re='作者: (.*)')  # 作者/author
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

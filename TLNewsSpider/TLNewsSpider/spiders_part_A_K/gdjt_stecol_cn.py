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



class GdjtStecolCnSpider(scrapy.Spider):
    name = 'gdjt.stecol.cn'
    allowed_domains = ['gdjt.stecol.cn']
    site_name = '中国电建'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页>资讯中心>电建要闻", "http://gdjt.stecol.cn/col/col3363/index.html"],
        ["企业舆情", "首页>资讯中心>企业要闻", "http://gdjt.stecol.cn/col/col3365/index.html"]
    ]
    custom_settings = {
        'DOWNLOAD_DELAY' : 2
    }

    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            #若不需要用到num来传递次数，则可删去
            meta = {'classification': classification,'num':1,'url':url}
            yield scrapy.Request(url, callback=self.parse, meta=meta,dont_filter=True)

    def parse(self, response):
        # 详情页
        text=re.findall('<h2>(.*?)</h2>',response.text)
        for tx in text:
            tx_time=re.findall('时间：(.*) </span>',tx)
            tx_url=re.findall('href="(.*)" target',tx)
            time_=''.join(tx_time)
            url_=''.join(tx_url)
            pagetime=date2time(date_str=time_)
            url=f"http://gdjt.stecol.cn{url_}"
            yield from over_page(url,response,page_num=1,callback=self.parse_detail)
            
        # #翻页
        response.meta['num']+=1
        next_url=f"{response.meta['url']}?uid=16324&pageNum={response.meta['num']}"
        yield from over_page(next_url, response, page_num=response.meta['num']-1, page_time=pagetime, callback=self.parse)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
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

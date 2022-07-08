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



class CnstockComSpider(scrapy.Spider):
    name = 'cnstock.com'
    allowed_domains = ['cnstock.com']
    site_name = '上海证券报'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 咨询库", "https://news.cnstock.com/news/sns_zxk/index.html"],
        ["企业舆情", "中国证券网 > 科创板 > 头条", "https://news.cnstock.com/kcb/skc_sbgsdt"],
        ["企业舆情", "中国证券网 > 上市公司 > 公司聚焦", "https://company.cnstock.com/company/scp_gsxw"],
        ["企业舆情", "中国证券网 > 上市公司 > 公告解读", "https://ggjd.cnstock.com/company/scp_ggjd/tjd_bbdj"],
        ["企业舆情", "中国证券网 > 上市公司 > 公告解读 > 公告快讯", "https://ggjd.cnstock.com/company/scp_ggjd/tjd_ggkx"]
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
        if 'sns_zxk/index.html' in response.url:
            for i in range(1,101):
                t=time.time()
                url=f"https://app.cnstock.com/api/waterfall?colunm=qmt-sns_zxk&page={i}&num=10&showstock=0&_={int(round(t * 1000))}"
                yield from over_page(url, response, callback=self.parse_cnstock,
                                     page_num=i)
                # yield scrapy.Request(url, callback=self.parse_cnstock, meta=response.meta)
                #
        elif 'kcb/skc_sbgsdt' in response.url:
            for i in range(1,101):
                t=time.time()
                url=f"https://app.cnstock.com/api/waterfall?colunm=qmt-skc_sbgsdt&page={i}&num=10&showstock=0&_={int(round(t * 1000))}"
                yield from over_page(url, response, callback=self.parse_cnstock,
                                     page_num=i)
                # yield scrapy.Request(url, callback=self.parse_cnstock, meta=response.meta)
                
                
        elif 'company/scp_gsxw' in response.url:
            for i in range(1,101):
                t=time.time()
                url=f"https://app.cnstock.com/api/waterfall?colunm=qmt-scp_gsxw&page={i}&num=10&showstock=0&_={int(round(t * 1000))}"
                yield from over_page(url, response, callback=self.parse_cnstock,
                                     page_num=i)
                # yield scrapy.Request(url, callback=self.parse_cnstock, meta=response.meta)
                
        elif 'company/scp_ggjd/tjd_bbdj' in response.url:
            for i in range(1,101):
                t=time.time()
                url=f"https://app.cnstock.com/api/waterfall?colunm=qmt-tjd_bbdj&page={i}&num=10&showstock=0&_={int(round(t * 1000))}"
                yield from over_page(url, response, callback=self.parse_cnstock,
                                     page_num=i)
                # yield scrapy.Request(url, callback=self.parse_cnstock, meta=response.meta)
                
        elif 'company/scp_ggjd/tjd_ggkx' in response.url:
            for i in range(1,101):
                t=time.time()
                url=f"https://app.cnstock.com/api/waterfall?colunm=qmt-tjd_ggkx&page={i}&num=10&showstock=0&_={int(round(t * 1000))}"
                yield from over_page(url, response, callback=self.parse_cnstock,
                                     page_num=i)
                # yield scrapy.Request(url, callback=self.parse_cnstock, meta=response.meta)

        

    # 首页>基金
    def parse_jijing(self, response):
        for url in response.css(".newslist_content li a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        for page in response.css('#Page a::attr(href),.pageControl a::attr(href)'):
            yield response.follow(page, meta=response.meta)

    # 首页 - 保险 - 行业公司
    def parse_cnstock(self, response):
        data=json.loads(response.text).get('data')
        for d in data.get('item'):
            url=d.get('link')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        sou=response.xpath('//span[@class="source"]//text()').getall()
        sou=''.join(sou)
        source=sou.replace('来源：','')
        item.add_value('article_source', source)  # 来源/article_source
        au=response.xpath('//span[@class="author"]//text()').getall()
        au=''.join(au)
        author=au.replace('作者：','')
        item.add_value('author', author)  # 作者/author
        # 默认保存一般无需更改
        item.add_value('spider_time', date())  # 抓取时间
        item.add_value('created_time', date())  # 更新时间
        item.add_value('source_url', response.url)  # 详情网址/detail_url
        item.add_value('site_name', self.site_name)  # 站点名称
        item.add_value('site_url', urlsplit(response.url).netloc)  # 站点host
        item.add_value('classification', response.meta['classification'])  # 所属分类
        # 网页源码  调试阶段注释方便查看日志
        item.add_value('html_text', response.text)  # 网页源码

        # 上面获取值可能为空, 追加匹配值
        # item.add_xpath('title', '//h1/text() || //p/h5/text()', re='[标题]{2}:(.*?)')  # 标题/title
        # item.add_css('publish_date', 'p:nth-last-child(-n+5)', re="[0-9]{0,4}年[0-9]{1,2}月[0-9]{1,2}日")  # 发布日期/publish_date
        return item.load_item()

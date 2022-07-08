# -*- coding: utf-8 -*-

import re
import time
import math
import scrapy
import json
from urllib.parse import urlsplit

from ..utils import date, over_page
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class CnfolComSpider(scrapy.Spider):
    name = 'cnfol.com'
    # allowed_domains = ['cnfol.com']
    site_name = '中金在线'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 财经 > 产业经济", "http://news.cnfol.com/chanyejingji/"],
        ["企业舆情", "首页>>市场>> 个股资讯", "http://sc.stock.cnfol.com/ggzixun/"],
        ["企业舆情", "首页 > 行业 > 产业综合", "http://hy.stock.cnfol.com/"],
        ["企业舆情", "首页 > 财经 > IT", "http://news.cnfol.com/it/"],
        ["企业舆情", "首页 > 银行 > 银行业内动态", "http://bank.cnfol.com/yinhangyeneidongtai/"],
        ["企业舆情", "首页 >  > 行业 >  > 行业综合", "http://hy.stock.cnfol.com/hangyezonghe/"],
        ["企业舆情", "首页 >  > 行业 >  >  产业综合", "http://hy.stock.cnfol.com/yuancailiao/"],
        ["行业舆情", "首页 >  > 行业 >  >  商业", "http://hy.stock.cnfol.com/bankuaijujiao/"],
        ["宏观舆情", "首页 > 黄金>行业", "http://gold.cnfol.com/hangyezixun/"],
        ["企业舆情", "首页  > 汽车 > 车市动态", "http://auto.cnfol.com/cheshidongtai/"]
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
        if 'http://hy.stock.cnfol.com/' == response.url:
            yield from self.parse_hy(response)
            
        elif 'cnfol.com/chanyejingji/' in response.url:
            for i in range(1,100):
                t = time.time()
                url=f"http://app.cnfol.com/test/newlist_api.php?catid=1280&page={i}&_={int(round(t * 1000))}"
                yield from over_page(url, response, page_num=i, callback=self.parse_newlist)
                # yield scrapy.Request(url, callback=self.parse_newlist, meta=response.meta)
               
        elif 'cnfol.com/ggzixun/' in response.url:
            for i in range(1,100):
                t = time.time()
                url=f"http://app.cnfol.com/test/newlist_api.php?catid=4035&page={i}&_={int(round(t * 1000))}"
                yield from over_page(url, response, page_num=i, callback=self.parse_newlist)
                # yield scrapy.Request(url, callback=self.parse_newlist, meta=response.meta)
                
        elif 'cnfol.com/it/' in response.url:
            for i in range(1,100):
                t = time.time()
                url=f"http://app.cnfol.com/test/newlist_api.php?catid=1587&page={i}&_={int(round(t * 1000))}"
                yield from over_page(url, response, page_num=i, callback=self.parse_newlist)
                # yield scrapy.Request(url, callback=self.parse_newlist, meta=response.meta)
                
        elif 'bank.cnfol' in response.url:
            for i in range(1,200):
                t = time.time()
                url=f"http://app.cnfol.com/test/newlist_api.php?catid=1410&page={i}&_={int(round(t * 1000))}"
                yield from over_page(url, response, page_num=i, callback=self.parse_newlist)
                # yield scrapy.Request(url, callback=self.parse_newlist, meta=response.meta)
                
        elif 'cnfol.com/hangyezonghe/' in response.url:
            for i in range(1,201):
                t = time.time()
                url=f"http://app.cnfol.com/test/newlist_api.php?catid=1469&page={i}&_={int(round(t * 1000))}"
                yield from over_page(url, response, page_num=i, callback=self.parse_newlist)
                # yield scrapy.Request(url, callback=self.parse_newlist, meta=response.meta)

        elif 'cnfol.com/yuancailiao/' in response.url:
            for i in range(1, 300):
                t = time.time()
                url = f"http://app.cnfol.com/test/newlist_api.php?catid=2441&page={i}&_={int(round(t * 1000))}"
                yield from over_page(url, response, page_num=i, callback=self.parse_newlist)
                # yield scrapy.Request(url, callback=self.parse_newlist, meta=response.meta)
                
        elif 'cnfol.com/bankuaijujiao/' in response.url:
            for i in range(1, 100):
                t = time.time()
                url = f"http://app.cnfol.com/test/newlist_api.php?catid=1329&page={i}&_={int(round(t * 1000))}"
                yield from over_page(url, response, page_num=i, callback=self.parse_newlist)
                # yield scrapy.Request(url, callback=self.parse_newlist, meta=response.meta)
                
        elif 'cnfol.com/bankuaijujiao/' in response.url:
            for i in range(1, 100):
                t = time.time()
                url = f"http://app.cnfol.com/test/newlist_api.php?catid=1329&page={i}&_={int(round(t * 1000))}"
                yield from over_page(url, response, page_num=i, callback=self.parse_newlist)
                # yield scrapy.Request(url, callback=self.parse_newlist, meta=response.meta)

        elif 'gold.cnfol.com/hangyezixun/' in response.url:
            t = time.time()
            url=f"http://shell.cnfol.com/article/gold_article.php?classid=2021&title=&start=0&end=250&apikey=&_={int(round(t * 1000))}"
            # yield from over_page(url, response, page_num=i, callback=self.parse_newlist)
            yield scrapy.Request(url, callback=self.parse_gold, meta=response.meta)
            
        elif 'cnfol.com/cheshidongtai/' in response.url:
            for i in range(1, 450):
                t = time.time()
                url = f"http://app.cnfol.com/test/newlist_api.php?catid=1691&page={i}&_={int(round(t * 1000))}"
                yield from over_page(url, response, page_num=i, callback=self.parse_newlist)
                # yield scrapy.Request(url, callback=self.parse_newlist, meta=response.meta)


    # 首页>基金
    def parse_hy(self, response):
        for url in response.xpath('//*[@id="artList"]/div/a[1]'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_newlist(self,response):
        data=json.loads(response.text)
        for d in data:
            url=d.get('Url')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
            
    def parse_gold(self,response):
        data = json.loads(response.text).get('content')
        for d in data:
            url = d.get('Url')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)


    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        content=response.xpath('//div[@class="Article"]//text()').getall()
        if content ==[]:
            content_=response.xpath('//div[@id="__content"]//text()').getall()
            content_text=[x.strip() for x in content_ if x.strip() != '']
            item.add_value('content_text', content_text)
        else:
            content_text = [x.strip() for x in content if x.strip() != '']
            item.add_value('content_text', content_text)
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="artDes"]/span[2]/text()',re='来源:(.*)')
        item.add_xpath('article_source', '//div[@class="newsDiv"]/div/span[2]/text()', re='来源：(.*)')
        item.add_xpath('author', '//*[@class="artDes"]/span[3]/text()',re='作者:(.*)')# 作者/author
        item.add_xpath('author', '//div[@class="newsDiv"]/div/span[3]/text()', re='作者：(.*)')  # 作者/author
        
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

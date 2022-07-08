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



class ChinagrainCnSpider(scrapy.Spider):
    name = 'chinagrain.cn'
    allowed_domains = ['chinagrain.cn']
    site_name = '中国粮油信息网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页>行业资讯",
         "http://www.chinagrain.cn/liangyou_news.htm?pageno=1&url=liangyou_news.htm&title=%E7%B2%AE%E6%B2%B9%E8%A1%8C%E4%B8%9A%E5%8A%A8%E6%80%81&type=1001&key=&newsnum=&producttype="],
        ["企业舆情", "首页>期货市场", "http://www.chinagrain.cn/futures/"]
    ]

    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            #若不需要用到num来传递次数，则可删去
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        #直接在parse里遍历页码的翻页
        if '/liangyou_news.htm?' in  response.url:
           for i in range(1,16):
               url=f"https://www.chinagrain.cn/liangyou_news.htm?pageno={i}&url=liangyou_news.htm&title=%E7%B2%AE%E6%B2%B9%E8%A1%8C%E4%B8%9A%E5%8A%A8%E6%80%81&type=1001&key=&newsnum=&producttype="
               yield from over_page(url,response,page_num=i,callback=self.parse_jijing)
               
        elif 'chinagrain.cn/futures/' in  response.url:
           for i in range(1,101):
               url=f"https://www.chinagrain.cn/liangyou_futures.htm?pageno={i}&url=liangyou_futures.htm&title=%E5%86%9C%E4%BA%A7%E5%93%81%E6%9C%9F%E8%B4%A7%E5%B8%82%E5%9C%BA&type=8001&key=&newsnum=&producttype="
               yield from over_page(url,response,page_num=i,callback=self.parse_jijing)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        for data  in response.xpath('//*[@class="left-side-items"]/li'):
            url=data.xpath('./a/@href').get()
            datatime=data.xpath('./span[2]/text()').get()
            dt=datatime.replace('时间：','')
            pagetime=date2time(time_str=dt)
            yield from over_page(url,response,page_num=1,page_time=pagetime,callback=self.parse_detail)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text','//*[@class="article-conte-infor"]//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="fl article-time"]/span[2]/text()',re='来源：(.*)')  # 来源/article_source
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

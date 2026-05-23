# -*- coding: utf-8 -*-
import datetime
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



class FinetHkSpider(scrapy.Spider):
    name = 'finet.hk'
    allowed_domains = ['finet.hk']
    site_name = '财华网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["宏观舆情", "主页>快讯>市场", "https://www.finet.hk/newscenter/market"],
        ["企业公告", "主页>快讯>公告", "https://www.finet.hk/newscenter/announcement"],
        ["宏观舆情", "主页>地产", "https://www.finet.hk/newscenter/properties"],
        ["宏观舆情", "主页>快讯>宏观", "https://www.finet.hk/newscenter/finance"]
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
        if '/newscenter/market' in response.url:
            for i in range(1,1000):
                url=f"https://www.finet.hk/newscenter/getCategoryNews/1000078/{i}"
                yield from over_page(url, response, page_num=i, callback=self.parse_finet)
                
        elif 'newscenter/announcement' in response.url:
            for i in range(1,1000):
                url=f"https://www.finet.hk/newscenter/getCategoryNews/1000226/{i}"
                yield from over_page(url, response, page_num=i, callback=self.parse_finet)

                
        elif 'newscenter/properties' in response.url:
            for i in range(1,1000):
                url=f"https://www.finet.hk/newscenter/getCategoryNews/1000005/{i}"
                yield from over_page(url, response, page_num=i, callback=self.parse_finet)

                
        elif 'newscenter/finance' in response.url:
            for i in range(1,1000):
                url=f"https://www.finet.hk/newscenter/getCategoryNews/1000000/{i}"
                yield from over_page(url, response, page_num=i, callback=self.parse_finet)


    def parse_finet(self, response):
        for data in json.loads(response.text):
            id=data.get('id')
            source_url=f"https://www.finet.hk/newscenter/news_content/{id}"
            response.meta['title_'] = data.get('title_sc')
            time_original_=data.get('publish_time')
            time_original=time_original_.replace('年',':').replace('月',':').replace('日','').replace('下午','PM:').replace('上午','AM:')
            time_format = datetime.datetime.strptime(time_original, '%Y:%m:%d %p:%I:%M')
            response.meta['time_format'] = time_format.strftime('%Y-%m-%d %H:%M')
            response.meta['content_text']=data.get('content_sc')
            yield response.follow(url=source_url, callback=self.parse_detail, meta=response.meta)
            

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        content_rules = ContentRules()
        item.add_value('title', response.meta['title_'])  # 标题/title
        item.add_value('publish_date', response.meta['time_format'])  # 发布日期/publish_date
        content=response.xpath('//*[@id="news_detail_wrapper"]/p/text()').getall()
        if content == []:
            content_ = response.xpath('//*[@id="news_detail_wrapper"]/text()').getall()
            content_text=''.join(content_)
            item.add_value('content_text',content_text)  # 正文内容/text_content
        else:
            content_text=''.join(content)
            item.add_value('content_text',content_text)  # 正文内容/text_content
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
        

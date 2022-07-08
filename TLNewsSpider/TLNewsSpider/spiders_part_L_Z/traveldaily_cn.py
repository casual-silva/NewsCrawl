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



class TraveldailyCnSpider(scrapy.Spider):
    name = 'traveldaily.cn'
    allowed_domains = ['traveldaily.cn']
    site_name = '环球旅讯峰会'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 行业 > OTA", "https://www.traveldaily.cn/ota/"],
        ["行业舆情", "首页 > 行业 > 住宿", "https://www.traveldaily.cn/hotel/"],
        ["行业舆情", "首页 > 行业 > 航空", "https://www.traveldaily.cn/airline/"],
        ["行业舆情", "首页 > 行业 > 旅游分销", "https://www.traveldaily.cn/distribute/"],
        ["行业舆情", "首页 > 行业 > 旅游科技", "https://www.traveldaily.cn/traveltech/"],
        ["行业舆情", "首页 > 行业 > 出行", "https://www.traveldaily.cn/mobility/"]
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
        if 'traveldaily.cn/ota/' in response.url:
            response.meta['id']='7'
            yield from self.parse_jijing(response)

        elif 'traveldaily.cn/hotel/' in response.url:
            response.meta['id']='5'
            yield from self.parse_jijing(response)
            
        elif 'traveldaily.cn/airline/' in response.url:
            response.meta['id']='4'
            yield from self.parse_jijing(response)
            
        elif 'traveldaily.cn/distribute/' in response.url:
            response.meta['id']='14'
            yield from self.parse_jijing(response)
        
        elif 'traveldaily.cn/traveltech/' in response.url:
            response.meta['id']='11'
            yield from self.parse_jijing(response)
            
        elif 'traveldaily.cn/mobility/' in response.url:
            response.meta['id']='2'
            yield from self.parse_jijing(response)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        for url in response.css("a.articleItemTitleLink"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        data_pub=response.xpath('//*[@class="articleItem clear"]/@data-pub').get()
        date_list=response.xpath('//*[@class="articleItemTime"]/text()').getall()
        next_url='https://www.traveldaily.cn/List/IndexMore'
        data={'id': response.meta['id'],'last': data_pub}
        page_time = date2time(date_str=date_list[-1])
        response.meta['num'] += 1
        yield from over_page(next_url, response, page_time=page_time, page_num=response.meta['num'],
                             callback=self.parse_jijing,formdata=data)
        

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text', '//*[@id="articleContent"]/p//text()|//*[@class="articleContent"]/p/a[not(@class)]/@href')  # 正文内容/text_content
        # 自定义规则
        # item.add_css('article_source', '.source .ly a:first-child::text')  # 来源/article_source
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

        # 上面获取值可能为空, 追加匹配值
        # item.add_xpath('title', '//h1/text() || //p/h5/text()', re='[标题]{2}:(.*?)')  # 标题/title
        # item.add_css('publish_date', 'p:nth-last-child(-n+5)', re="[0-9]{0,4}年[0-9]{1,2}月[0-9]{1,2}日")  # 发布日期/publish_date
        return item.load_item()

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



class ChinaCottonOrgSpider(scrapy.Spider):
    name = 'china-cotton.org'
    allowed_domains = ['china-cotton.org']
    site_name = '中国棉花协会'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 棉花资讯 > 国内棉花", "http://www.china-cotton.org/advise/china_cotton_list"],
        ["行业舆情", "首页 > 棉花资讯 > 国际棉花", "http://www.china-cotton.org/advise/inter_cotton_list"],
        ["行业舆情", "首页 > 棉花资讯 > 纺织信息", "http://www.china-cotton.org/advise/textile_cotton_list"],
        ["宏观舆情", "首页 > 棉花资讯 > 宏观经济", "http://www.china-cotton.org/advise/eco_cotton_list"]
    ]
    
    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification,'index_url':url}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        for i in range(1,1000):
            url=f"{response.meta['index_url']}/20/{i}"
            yield from over_page(url, response, page_num=i, callback=self.parse_cotton)
            # yield response.follow(url, callback=self.parse_cotton, meta=response.meta)

    def parse_cotton(self, response):
        url_list=response.xpath('//*[@class="special-li"]/a/@href').getall()
        for url in url_list:
            if 'javascript' in url:
                print(url)
                print('此新闻只针对会员开放，如已是会员,请点击确认登陆!')
            else:
                yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title', '//*[@class="border article"]//h1/text()')  # 标题/title
        date_= self.publish_date_rules.extractor(response.text)
        publish_date=date_.replace('年','-').replace('月','-').replace('日','')
        item.add_value('publish_date',publish_date)  # 发布日期/publish_date
        content=response.xpath('//*[@class="txt"]//text()').getall()
        content_text=[x.strip() for x in content if x.strip() != '']
        item.add_value('content_text', content_text)  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="article-time"]/span[1]/text()',re='出处：(.*)')  # 来源/article_source
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

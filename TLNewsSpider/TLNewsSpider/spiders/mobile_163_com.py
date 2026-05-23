# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
from ..utils import date
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor

class Mobile163ComSpider(scrapy.Spider):
    name = 'mobile.163.com'
    site_name = '网易'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ['企业舆情', '首页 > 网易手机', 'https://mobile.163.com'],
        ['宏观舆情', '网易首页 > 网易财经 > 宏观新闻', 'https://money.163.com/special/00252G50/macro.html'],
        ['企业公告', '网易首页 > 网易财经 > 公告精选', 'https://money.163.com/special/ggjx/#/home'],
        ['行业舆情', '网易首页 > 网易财经 > 行业板块', 'https://money.163.com/special/00251LJV/hyyj.html'],
        ['企业舆情', '网易首页 > 网易财经 > 个股资讯', 'https://money.163.com/special/g/00251LR5/gptj.html']
    ]

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'mobile.163.com' in response.url:
            url=f"https://mobile.163.com/special/index_datalist/?callback=data_callback"
            yield scrapy.Request(url,callback=self.parse_mobile,meta=response.meta)
            for i in range(1, 5):
                url = f"https://mobile.163.com/special/index_datalist_0{i}/?callback=data_callback"
                yield scrapy.Request(url=url, callback=self.parse_mobile, meta=response.meta)

        elif 'macro.html' in response.url:
            yield from self.parse_macro(response)
        
        elif 'hyyj.html' in response.url:
            yield from self.parse_macro(response)
        
        elif 'gptj.html' in response.url:
            yield from self.parse_macro(response)
            
        elif 'ggjx'in response.url:
            yield from self.parse_ggjx(response)

    # 首页>基金
    def parse_mobile(self, response):
        list=[]
        datas = re.findall(".*?({.*}).*", response.text, re.S)
        pattern = re.findall('"docurl":"[a-zA-z]+://[^\s]*"',str(datas))
        for p in pattern:
            url_= re.findall('[a-zA-z]+://[^\s]*', p)
            url=str(url_).replace('"','').replace(']','').replace('[','').replace("'","")
            yield scrapy.Request(url=url,callback=self.parse_detail,meta=response.meta)

    def parse_macro(self, response):
        for url in response.css(".item_top h2 a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
        # 翻页
        for page in response.xpath('//*[@title="下一页"]/@href'):
            yield response.follow(page,callback=self.parse_macro,meta=response.meta)


    # 首页 - 保险 - 行业公司
    def parse_ggjx(self, response):
        a = re.findall('list:([\s\S]*) \]', response.text, re.S)
        urls=re.findall('"link": "[a-zA-z]+://[^\s]*"',str(a),re.S)
        for u in urls:
            url=str(re.findall('[a-zA-z]+://[^\s]*',u,re.S)).replace('"','').replace(']','').replace('[','').replace("'","")
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
                
        for page in response.xpath('//*[@title="下一页"]/@href'):
            yield response.follow(page,callback=self.parse_macro,meta=response.meta)
        
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source','//*[@class="post_info"]/text()',re='[来源]:(.*)')  # 来源/article_source
        item.add_xpath('article_source','//*[@class="post_info"]/a[1]/text()')
        item.add_xpath('author', '//*[@class="post_author"]/a/img/@alt')  # 作者/author
        
        # 默认保存一般无需更改
        item.add_value('spider_time', date())  # 抓取时间
        item.add_value('created_time', date())  # 更新时间
        item.add_value('source_url', response.url)  # 详情网址/detail_url
        item.add_value('site_name', self.site_name)  # 站点名称
        item.add_value('site_url', urlsplit(response.url).netloc)  # 站点host
        item.add_value('classification', response.meta['classification'])  # 所属分类
        # 网页源码  调试阶段注释方便查看日志
        # item.add_value('html_text', response.text)  # 网页源码

        # 上面获取值可能为空, 追加匹配值
        # item.add_xpath('title', '//h1/text() || //p/h5/text()', re='[标题]{2}:(.*?)')  # 标题/title
        # item.add_css('publish_date', 'p:nth-last-child(-n+5)', re="[0-9]{0,4}年[0-9]{1,2}月[0-9]{1,2}日")  # 发布日期/publish_date
        return item.load_item()

# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time

from ..utils import date
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class TexnetComCnSpider(scrapy.Spider):
    name = 'texnet.com.cn'
    # allowed_domains = ['texnet.com.cn','texindex.com.cn']
    site_name = '纺织网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 企业动态", "http://info.texnet.com.cn/list--13-1.html"],
        ["企业舆情", "首页 > 企业资讯", "http://www.texindex.com.cn/news/qyzx/"],
        ["企业舆情", "首页 > 资讯家纺 > 家纺企业", "http://info.texnet.com.cn/jf_list-12-1.html"],
        ["企业舆情", "首页 > 资讯服装 > 服装企业", "http://info.texnet.com.cn/fz_list-12-1.html"],
        ["行业舆情", "首页 > 纺机专区", "http://info.texnet.com.cn/list-18--1.html"],
        ["行业舆情", "首页 > 无纺专区", "http://info.texnet.com.cn/list-12--1.html"],
        ["行业舆情", "首页 > 染整专区", "http://info.texnet.com.cn/list-13--1.html"]
    ]

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'texnet.com.cn/list-' in response.url:
            yield from self.parse_list(response)

        elif '/news/qyzx/' in response.url:
            yield from self.parse_qyzx(response)
            
        elif '/jf_list' or '/fz_list' in response.url:
            yield from self.parse_jf(response)

    # 首页>基金
    def parse_list(self, response):
        for url in response.css(".content-list ul li a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        for page in response.xpath('//a[text()="下一页"]'):
            yield response.follow(page, meta=response.meta)

    # 首页 - 保险 - 行业公司
    def parse_qyzx(self, response):
        for url in response.css(".RightItemBody td.InnerLink a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
        # 翻页
        for page in response.xpath('//a[text()="[下一页]"]'):
            yield response.follow(page, meta=response.meta)

    def parse_jf(self, response):
        for url in response.css(".content-list2 ul li a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
        # 翻页
        for page in response.xpath('//a[text()="下一页"]'):
            yield response.follow(page, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title', '//*[@class="line40 fontwei font24 fontblack"]/text()')  # 标题/title
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        pd=self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('年','-').replace('月','-').replace('日','').replace('\xa0',' ')
        item.add_value('publish_date', publish_date)  # 发布日期/publish_date
        content=response.xpath('//*[@class="detail-text line25 font14px"]/div//text()').getall()
        content_qyzx=response.xpath('//*[@id="zoom"]/p//text()').getall()
        if content != []:
            content_text =[x.strip() for x in content if x.strip() != '']
            item.add_value('content_text', content_text)
        elif content_qyzx !=[]:
            content_text = [x.strip() for x in content_qyzx if x.strip() != '']
            item.add_value('content_text', content_text)
        elif content and content_jf ==[]:
            item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="line22 fontgrey"]/text()',re='来源：(.*)')  # 来源/article_source
        item.add_value('author',self.author_rules.extractor(response.text))  # 作者/author
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

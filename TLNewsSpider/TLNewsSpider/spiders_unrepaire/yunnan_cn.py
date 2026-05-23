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



class YunnanCnSpider(scrapy.Spider):
    name = 'yunnan.cn'
    allowed_domains = ['yunnan.cn']
    site_name = '云南网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["地区舆情", "首页 > 新闻>云南", "http://society.yunnan.cn/ynkd/"],
        ["宏观舆情", "首页 > 新闻>国内", "http://news.yunnan.cn/gn/index.shtml"],
        ["宏观舆情", "首页 > 新闻>国际", "http://news.yunnan.cn/gj/index.shtml"],
        ["地区舆情", "云南网 > 财经 > 滇企", "http://finance.yunnan.cn/dq/"],
        ["行业舆情", "云南网 > 财经 > 银行", "http://finance.yunnan.cn/yh/index.shtml"],
        ["行业舆情", "云南网 > 财经 > 保险", "http://finance.yunnan.cn/bx/index.shtml"],
        ["宏观舆情", "云南网 > 财经 > 产经", "http://finance.yunnan.cn/cj/index.shtml"]
    ]

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'ynkd' in response.url:
            response.meta['url_']='http://society.yunnan.cn/system/count//0007007/000000000000/000/'
            response.meta['url_p'] ='/c0007007000000000000_00000'
            yield from self.parse_yunnan(response)

        elif '/gn/' in response.url:
            response.meta['url_'] = 'http://news.yunnan.cn/system/count//0004003/000000000000/000/'
            response.meta['url_p']='/c0004003000000000000_00000'
            yield from self.parse_yunnan(response)
            
        elif '/gj/' in response.url:
            response.meta['url_'] = 'http://news.yunnan.cn/system/count//0004004/000000000000/000/'
            response.meta['url_p']='/c0004004000000000000_00000'
            yield from self.parse_yunnan(response)
            
        elif '/dq/' in response.url:
            response.meta['url_'] = 'http://finance.yunnan.cn/system/count//0015008/000000000000/000/'
            response.meta['url_p']='/c0015008000000000000_00000'
            yield from self.parse_yunnan(response)
            
        elif '/cj/' in response.url:
            response.meta['url_'] = 'http://finance.yunnan.cn/system/count//0015011/000000000000/000/'
            response.meta['url_p']='/c0015011000000000000_00000'
            yield from self.parse_yunnan(response)
            
        elif '/bx/' in response.url:
            response.meta['url_'] = 'http://finance.yunnan.cn/system/count//0015009/000000000000/000/'
            response.meta['url_p']='/c0015009000000000000_00000'
            yield from self.parse_yunnan(response)
            
        elif '/yh/' in response.url:
            response.meta['url_'] = 'http://finance.yunnan.cn/system/count//0015010/000000000000/000/'
            response.meta['url_p']='/c0015010000000000000_00000'
            yield from self.parse_yunnan(response)


    # 首页>基金
    def parse_yunnan(self, response):
        for url in response.css(".fs1 a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        page=response.xpath('//*[@class="xleft fl"]/script/@src').get()
        yield response.follow(page,callback=self.parse_next ,meta=response.meta)
    
    def parse_next(self, response):
        code=re.findall('maxpage = (\d+);',response.text)
        code_=''.join(code)
        max_page=int(code_)+ 1
        for i in range(1,max_page):
            if  4999< i < 6000:
                url=f"{response.meta['url_']}005{response.meta['url_p']}{i}.shtml"
                yield scrapy.Request(url, callback=self.parse_url, meta=response.meta)
            elif  3999< i < 5000:
                url=f"{response.meta['url_']}004{response.meta['url_p']}{i}.shtml"
                yield scrapy.Request(url, callback=self.parse_url, meta=response.meta)
                
            elif  2999< i < 4000:
                url=f"{response.meta['url_']}003{response.meta['url_p']}{i}.shtml"
                yield scrapy.Request(url, callback=self.parse_url, meta=response.meta)
                
            elif  1999< i < 3000:
                url=f"{response.meta['url_']}002{response.meta['url_p']}{i}.shtml"
                yield scrapy.Request(url, callback=self.parse_url, meta=response.meta)
                
            elif  999< i < 2000:
                url=f"{response.meta['url_']}001{response.meta['url_p']}{i}.shtml"
                yield scrapy.Request(url,callback=self.parse_url,meta=response.meta)
                
            elif 99 < i < 1000 :
                url = f"{response.meta['url_']}000{response.meta['url_p']}0{i}.shtml"
                yield scrapy.Request(url, callback=self.parse_url, meta=response.meta)
                
            elif 9 < i < 100 :
                url = f"{response.meta['url_']}000{response.meta['url_p']}00{i}.shtml"
                yield scrapy.Request(url, callback=self.parse_url, meta=response.meta)
            
            elif i < 10 :
                url = f"{response.meta['url_']}000{response.meta['url_p']}000{i}.shtml"
                yield scrapy.Request(url, callback=self.parse_url, meta=response.meta)
            
    def parse_url(self,response):
        for url in response.css(".fs1 a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title','//*[@class="xt yh"]/text()')  # 标题/title
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        pd=self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('年','-').replace('月','-').replace('日','')
        item.add_value('publish_date',publish_date )  # 发布日期/publish_date
        content=response.xpath('//*[@class="xcont ohd clear"]//p//text()').getall()
        content_text=[x.strip() for x in content if x.strip() != '']
        item.add_value('content_text',content_text)  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="xt2 yh fl"]/span[2]/text()')  # 来源/article_source
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

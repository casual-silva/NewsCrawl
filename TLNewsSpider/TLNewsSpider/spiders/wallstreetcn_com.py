# -*- coding: utf-8 -*-
import random
import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time
from lxml import etree
from .. import settings
from ..utils import date
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor


class WallstreetcnComSpider(scrapy.Spider):
    name = 'wallstreetcn.com'
    site_name = '华尔街见闻'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()
    
    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 资讯 > 公司", "https://wallstreetcn.com/news/enterprise"],
        ["行业舆情", "首页 > 资讯 > 地产", "https://wallstreetcn.com/news/estate"],
        ["行业舆情", "首页 > 资讯 > 汽车", "https://wallstreetcn.com/news/car"],
        ["行业舆情", "首页 > 资讯 > 医药", "https://wallstreetcn.com/news/medicine"]
    ]

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        if 'news/enterprise' in response.url:
            url='https://api-one.wallstcn.com/apiv1/content/information-flow?channel=enterprise&cursor=&accept=article&limit=20&action=upglide'
            yield scrapy.Request(url, callback=self.parse_news, meta=response.meta)

        elif 'news/estate' in response.url:
            url = 'https://api-one.wallstcn.com/apiv1/content/information-flow?channel=estate&accept=article&cursor=&limit=20&action=upglide'
            yield scrapy.Request(url, callback=self.parse_news, meta=response.meta)
            
        elif 'news/car' in response.url:
            url = 'https://api-one.wallstcn.com/apiv1/content/information-flow?channel=car&accept=article&cursor=&limit=20&action=upglide'
            yield scrapy.Request(url, callback=self.parse_news, meta=response.meta)
            
        elif 'news/medicine' in response.url:
            url = 'https://api-one.wallstcn.com/apiv1/content/information-flow?channel=medicine&cursor=&accept=article&limit=20&action=upglide'
            yield scrapy.Request(url, callback=self.parse_news, meta=response.meta)
    
    def parse_news(self, response):
        data=json.loads(response.text).get('data')
        next_cursor=data.get('next_cursor')
        next_url = f"https://api-one.wallstcn.com/apiv1/content/information-flow?channel=enterprise&cursor={next_cursor}&accept=article&limit=20&action=upglide"
        yield response.follow(next_url, callback=self.parse_news, meta=response.meta)
        
        items=data.get('items')
        for item in items:
            resource=item.get('resource')
            url=resource.get('uri')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)


    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        title=response.xpath('//h1[@class="title"]/text()').get()
        code = re.findall('articles/([1-9]\d*)', response.url)
        code_ = ''.join(code)
        code_url = f"https://api-one.wallstcn.com/apiv1/content/articles/{code_}?extract=0&accept_theme=theme%2Cpremium-theme"
        # 通用提取规则
        if title:
            content_rules = ContentRules()  # 正文初始化 每次都需要初始化
            # item.add_xpath('title', '//h1[@class="title"]/text()')
            item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
            item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
            item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
            # 自定义规则
            item.add_css('article_source', '.source .ly a:first-child::text')  # 来源/article_source
            item.add_value('author', self.author_rules.extractor(response.text))  # 作者/author
            # 默认保存一般无需更改
            item.add_value('spider_time', date())  # 抓取时间
            item.add_value('created_time', date())  # 更新时间
            item.add_value('source_url', response.url)  # 详情网址/detail_url
            item.add_value('site_name', self.site_name)  # 站点名称
            item.add_value('site_url', urlsplit(response.url).netloc)  # 站点host
            item.add_value('classification', response.meta['classification'])  # 所属分类
            return item.load_item()
        else:
            yield scrapy.Request(code_url,callback=self.parse_code, meta=response.meta)
        
        # 网页源码  调试阶段注释方便查看日志
        # item.add_value('html_text', response.text)  # 网页源码

        # 上面获取值可能为空, 追加匹配值
        # item.add_xpath('title', '//h1/text() || //p/h5/text()', re='[标题]{2}:(.*?)')  # 标题/title
        # item.add_css('publish_date', 'p:nth-last-child(-n+5)', re="[0-9]{0,4}年[0-9]{1,2}月[0-9]{1,2}日")  # 发布日期/publish_date
        
    def parse_code(self,response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        data=json.loads(response.text).get('data')
        author=data.get('author')
        author_=author.get('display_name')
        display_time=data.get('display_time')
        timeArray = time.localtime(display_time)
        publish_date = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        content=data.get('content')
        content_=etree.HTML(content)
        content_text=''.join(content_.xpath('string(.)'))
        title=data.get('title')
        item.add_value('title', title)  # 标题/title
        item.add_value('publish_date', publish_date)  # 发布日期/publish_date
        item.add_value('content_text', content_text)  # 正文内容/text_content
        # 自定义规则
        item.add_value('author', author_)  # 作者/author
        # 默认保存一般无需更改
        item.add_value('spider_time', date())  # 抓取时间
        item.add_value('created_time', date())  # 更新时间
        item.add_value('source_url', response.url)  # 详情网址/detail_url
        item.add_value('site_name', self.site_name)  # 站点名称
        item.add_value('site_url', urlsplit(response.url).netloc)  # 站点host
        item.add_value('classification', response.meta['classification'])  # 所属分类
        return item.load_item()
        
    
# -*- coding: utf-8 -*-
import json
import re
import math
import scrapy
from urllib.parse import urlsplit

from ..utils import date, over_page
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class CcidcomComSpider(scrapy.Spider):
    name = 'ccidcom.com'
    allowed_domains = ['ccidcom.com']
    site_name = '赛迪通信产业网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 公司", "http://www.ccidcom.com/company/index.html"],
        ["企业舆情", "首页 > 要闻", "http://www.ccidcom.com/yaowen/index.html"]
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
        if '/company/index.html' in response.url:
        #post请求的遍历页码的翻页
            for i in range(0,1000,10):
                url='http://www.ccidcom.com/getcolumnarts.do'
                data={'colnum_name': 'company','start':str(i),'page': '1','csrf625550324b3a1': '43f30c683a7d025be0259a5ec9dfeee8'}
                num = i / 10
                yield from over_page(url,response,callback=self.parse_jijing,formdata=data,page_num=num)
        
        if '/yaowen/index.html' in response.url:
            for i in range(0, 2000, 10):
                url = 'http://www.ccidcom.com/getcolumnarts.do'
                data = {'colnum_name': 'yaowen', 'start': str(i), 'page': '1',
                        'csrf625552857b271': '9663b997370d8fb34c0e3351e6d584a8'}
                num = i / 10
                yield from over_page(url, response, callback=self.parse_jijing, formdata=data,
                                     page_num=num)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        arts=json.loads(response.text).get('arts')
        for ar in arts:
            url=ar.get('art_url')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
       
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="source"]/text()')  # 来源/article_source
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

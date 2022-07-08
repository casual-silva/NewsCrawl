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
from lxml import etree


class ZgyhyComCnSpider(scrapy.Spider):
    name = 'zgyhy.com.cn'
    allowed_domains = ['zgyhy.com.cn']
    site_name = '中国银行业'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页>资讯 > 行业", "http://www.zgyhy.com.cn/zixun/industry?11"],
        ["宏观舆情", "首页>资讯 > 宏观", "http://www.zgyhy.com.cn/zixun/macroscopic?3"],
        ["宏观舆情", "首页>资讯 > 地方", "http://www.zgyhy.com.cn/zixun/place?4"]
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
        #直接在parse里遍历页码的翻页
        if '/industry?11' in  response.url:
           for i in range(1,21):
               url=f"http://www.zgyhy.com.cn/zixun_all?id=11&pagenum={i}&numberStr=10"
               yield from over_page(url,response,page_num=i,callback=self.parse_jijing)
               
        elif '/macroscopic?3' in  response.url:
           for i in range(1,11):
               url=f"http://www.zgyhy.com.cn/zixun_all?id=3&pagenum={i}&numberStr=10"
               yield from over_page(url,response,page_num=i,callback=self.parse_jijing)
               
        elif '/place?4' in  response.url:
           for i in range(1,11):
               url=f"http://www.zgyhy.com.cn/zixun_all?id=4&pagenum={i}&numberStr=10"
               yield from over_page(url,response,page_num=i,callback=self.parse_jijing)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        #无法实现时间限制
        list=json.loads(response.text).get('list')
        for li in list:
            content=li.get('content')
            title=li.get('title')
            id=li.get('id')
            author=li.get('author')
            createTime=li.get('createTime')
            publish_date=createTime.replace('T',' ').replace('.000Z','')
            content_url=f"http://www.zgyhy.com.cn/zixun/zixun_xq?7{id}"
            html=etree.HTML(content)
            content_text=html.xpath('//text()')
            response.meta['content']=content_text
            response.meta['title']=title
            response.meta['content_url']=content_url
            response.meta['publish_date']=publish_date
            response.meta['author']=author
            yield response.follow(content_url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        item.add_value('title',response.meta['title'])  # 标题/title
        item.add_value('publish_date', response.meta['publish_date'])  # 发布日期/publish_date
        item.add_value('content_text', response.meta['content'])  # 正文内容/text_content
        # 自定义规则
        item.add_value('author',response.meta['author'])  # 作者/author
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

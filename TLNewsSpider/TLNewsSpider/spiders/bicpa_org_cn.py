# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time

from ..utils import date,over_page
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class BicpaOrgCnSpider(scrapy.Spider):
    name = 'bicpa.org.cn'
    allowed_domains = ['bicpa.org.cn']
    site_name = '北京注册会计师协会'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 >> 动态聚焦 >> 行业动态", "http://www.bicpa.org.cn/dtzj/hydt/index.html"]
    ]
    
    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification,'num':0}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        for i in range(0,500,15):
            url='http://www.bicpa.org.cn/dtzj/hydt/getArticles.action'
            data={'_q': 'Article.list','siteId': '7e0b3b27-2622-4aa7-b6f8-abfe5c5df922','catalogId': '83d33689-7b01-4c24-992e-d527845e8b6e',
                  'pub': 'true','limit': '15','start': str(i)}
            response.meta['num'] +=1
            yield from over_page(url,response,callback=self.parse_Articles,formdata=data,page_num=response.meta['num'])

    # 首页 - 保险 - 行业公司
    def parse_Articles(self, response):
        datas=re.findall('datas:(.*),total',response.text)
        for data in datas:
            list=json.loads(data)
            for li in list:
                primaryKey=li.get('primaryKey')
                url=f"http://www.bicpa.org.cn/dtzj/hydt/{primaryKey}.html"
                yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title', '//*[@class="headword"]/text()')  # 标题/title
        date_ = self.publish_date_rules.extractor(response.text)
        publish_date = date_.replace('年', '-').replace('月', '-').replace('日', '')
        item.add_value('publish_date', publish_date)  # 发布日期/publish_date
        content=response.xpath('//*[@id="art_content"]//text()').getall()
        content_text=[x.strip() for x in content if x.strip() != '']
        item.add_value('content_text',content_text)  # 正文内容/text_content
        # 自定义规则
        item.add_css('article_source', '.source .ly a:first-child::text')  # 来源/article_source
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

# -*- coding: utf-8 -*-

import re
import math

import demjson
import scrapy
from urllib.parse import urlsplit
import json
import time
from lxml import etree
from ..utils import date, over_page
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class CsindexComCnSpider(scrapy.Spider):
    name = 'csindex.com.cn'
    # allowed_domains = ['csindex.com.cn']
    site_name = '中证指数有限公司'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业公告", "首页>关于我们>新闻与公告", "https://www.csindex.com.cn/#/about/newsCenter/"]
    ]
    headers={
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
        "Content-Type": "application/json",
    }
    
    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        for i in range(1,101):
            payload={"lang": "cn",
                     "page": {"key": "","page": i,"rows": 10},
                     "classList": [],
                     "indexList": [],
                     "relatedTopics": [],
                     "typeList": []
                     }
            url="https://www.csindex.com.cn/csindex-home/announcement/queryAnnouncementByVo"
            yield scrapy.Request(url=url,method="POST", meta=response.meta,callback=self.parse_csin,body=demjson.encode(payload),headers=self.headers)

    # 首页>基金
    def parse_csin(self, response):
        data=json.loads(response.text).get('data')
        for d in data:
            id=d.get('id')
            url=f"https://www.csindex.com.cn/csindex-home/announcement/queryAnnouncementById?id={id}"
            yield response.follow(url, callback=self.parse_detail, meta=response.meta,headers=self.headers)
            

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        data = json.loads(response.text).get('data')
        title=data.get('title')
        item.add_value('title', title)  # 标题/title
        publish_date=data.get('publishDate')
        item.add_value('publish_date', publish_date)  # 发布日期/publish_date
        content=data.get('content')
        content_ = etree.HTML(content)
        content_text = ''.join(content_.xpath('string(.)'))
        item.add_value('content_text', content_text)  # 正文内容/text_content
        contentSource=data.get('contentSource')
        item.add_value('article_source', contentSource)  # 来源/article_source
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

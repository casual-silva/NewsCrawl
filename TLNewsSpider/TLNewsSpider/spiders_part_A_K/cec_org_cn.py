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


class CecOrgCnSpider(scrapy.Spider):
    name = 'cec.org.cn'
    allowed_domains = ['cec.org.cn']
    site_name = '中国电力企业联合会'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["宏观舆情", "首页>新闻中心>要闻快递>行业要闻", "https://cec.org.cn/menu/index.html?686"],
        ["行业舆情", "首页>新闻中心>行业成就", "https://cec.org.cn/menu/index.html?173"]
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
        #直接在parse里遍历页码的翻页
        if '/index.html?686' in  response.url:
           for i in range(1,11):
               url=f"https://cec.org.cn/ms-mcms/mcms/content/list?id=687&pageNumber=8&pageSize=10"
               yield from over_page(url,response,page_num=i,callback=self.parse_jijing)
               
        elif '/index.html?173' in  response.url:
           for i in range(1,26):
               url=f"https://cec.org.cn/ms-mcms/mcms/content/list?id=173&pageNumber={i}&pageSize=10"
               yield from over_page(url,response,page_num=i,callback=self.parse_jijing)


    # 下一页的翻页方式
    def parse_jijing(self, response):
        data=json.loads(response.text).get('data')
        list=data.get('list')
        for li in list:
            articleID=li.get('articleID')
            publicTime=li.get('publicTime')
            pagetime=date(publicTime)
            page_time=date2time(time_str=pagetime)
            response.meta['pagetime']=pagetime
            url=f"https://cec.org.cn/ms-mcms/mcms/content/detail?id={articleID}"
            yield from over_page(url,response,page_num=1,page_time=page_time,callback=self.parse_detail)

    def parse_detail(self, response):
        #从异步中获取数据
        data=json.loads(response.text).get('data')
        title=data.get('basicTitle')
        source=data.get('source')
        articleContent=data.get('articleContent')
        html=etree.HTML(articleContent)
        content=html.xpath('//text()')
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        item.add_value('title', title)  # 标题/title
        item.add_value('publish_date',response.meta['pagetime'])  # 发布日期/publish_date
        item.add_value('content_text', content)  # 正文内容/text_content
        # 自定义规则
        item.add_value('article_source',source)  # 来源/article_source
        # 默认保存一般无需更改
        item.add_value('spider_time', date())  # 抓取时间
        item.add_value('created_time', date())  # 更新时间
        item.add_value('source_url', response.url)  # 详情网址/detail_url
        item.add_value('site_name', self.site_name)  # 站点名称
        item.add_value('site_url', urlsplit(response.url).netloc)  # 站点host
        item.add_value('classification', response.meta['classification'])  # 所属分类
        # 网页源码  调试阶段注释方便查看日志
        item.add_value('html_text', response.text)  # 网页源码
        return item.load_item()

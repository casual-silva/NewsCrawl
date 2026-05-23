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



class GelonghuiComSpider(scrapy.Spider):
    name = 'gelonghui.com'
    allowed_domains = ['gelonghui.com']
    site_name = '格隆汇'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 事件>公司信息", "https://www.gelonghui.com/news/?type=33"],
        ["企业舆情", "首页 > 事件>港股异动", "https://www.gelonghui.com/news/?type=32"]
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
        if 'news/?type=33' in response.url:
            url='https://www.gelonghui.com/api/news?count=15&type=33'
            response.meta['code'] = '33'
            yield scrapy.Request(url=url, callback=self.parse_gelonghui, meta=response.meta)
            
        elif 'news/?type=32' in response.url:
            url='https://www.gelonghui.com/api/news?count=15&type=32'
            response.meta['code']='32'
            yield scrapy.Request(url=url, callback=self.parse_gelonghui, meta=response.meta)

    def parse_gelonghui(self, response):
        result=json.loads(response.text).get('result')
        for  r in result:
            id=r.get('id')
            timestamp=r.get('createDate')-1
            url=f"https://www.gelonghui.com/news/{id}"
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        #新的请求加载是上一个异步数据result里最后一个发布时间戳减1
        next_url=f"https://www.gelonghui.com/api/news?timestamp={timestamp}&count=15&type={response.meta['code']}"
        response.meta['num'] += 1
        yield from over_page(next_url, response, page_num=response.meta['num'], callback=self.parse_gelonghui)
        # yield scrapy.Request(url=next_url, callback=self.parse_gelonghui, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        pd=self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('年','-').replace('月','-').replace('日','')
        item.add_value('publish_date',publish_date )  # 发布日期/publish_date
        content=response.xpath('//*[@class="main-news article-with-html"]//text()').getall()
        content_text=[x.strip() for x in content if x.strip() != '']
        item.add_value('content_text', content_text)  # 正文内容/text_content
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

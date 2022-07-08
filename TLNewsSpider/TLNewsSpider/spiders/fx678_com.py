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



class Fx678ComSpider(scrapy.Spider):
    name = 'fx678.com'
    allowed_domains = ['fx678.com']
    site_name = '汇通财经'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 要闻", "https://news.fx678.com/"]
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
        yield from self.parse_jijing(response)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        for url in response.css("a.content"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        last_id=response.xpath('//*[@id="last_id"]/text()').get()
        next_url='https://news.fx678.com/index.php/more'
        newsTime=date2time(time_str=last_id)
        data={'newsTime': str(newsTime)}
        yield scrapy.FormRequest(next_url,callback=self.parse_baoxian,meta=response.meta,formdata=data)

    # 遍历url翻页方式
    def parse_baoxian(self, response):
        data=json.loads(response.text)
        for d in data:
            NewsUrl=d.get('NewsUrl')
            NEWSTIME=d.get('NEWSTIME')
            yield response.follow(NewsUrl, callback=self.parse_detail, meta=response.meta)
        psge_time=date2time(time_str=NEWSTIME)
        next_url = 'https://news.fx678.com/index.php/more'
        data={'newsTime': str(psge_time)}
        response.meta['num'] +=1
        yield from over_page(next_url,response,callback=self.parse_baoxian,page_time=psge_time,page_num=response.meta['num'],formdata=data)
        

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text','//*[@class="content"]//text()')  # 正文内容/text_content
        # 自定义规则
        # item.add_css('article_source', '.source .ly a:first-child::text')  # 来源/article_source
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

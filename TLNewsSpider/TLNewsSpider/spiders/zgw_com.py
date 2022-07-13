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



class ZgwComSpider(scrapy.Spider):
    name = 'zgw.com'
    allowed_domains = ['zgw.com']
    site_name = '中钢网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["宏观舆情", "首页>新闻中心>行业聚焦>宏观经济", "http://news.zgw.com/hgjj/"],
        ["行业舆情", "首页>新闻中心>行业聚焦>中钢网简评", "http://news.zgw.com/zgwjp/"],
        ["行业舆情", "首页>新闻中心>行业聚焦>钢铁新闻", "http://news.zgw.com/gtxw/"],
        ["行业舆情", "首页>新闻中心>行业聚焦>钢厂动态", "http://news.zgw.com/gcdt/"],
        ["行业舆情", "首页>新闻中心>行业聚焦>国际要闻", "http://news.zgw.com/gjyw/"],
        ["行业舆情", "首页>新闻中心>行业聚焦>中钢网视点", "http://news.zgw.com/zgwsd/"],
        ["行业舆情", "首页>新闻中心>行业聚焦>期货专栏", "http://news.zgw.com/qhzl/"],
        ["行业舆情", "首页>新闻中心>行业聚焦>机构点评", "http://news.zgw.com/jgdp/"],
        ["行业舆情", "首页>新闻中心>行业聚焦>原料新闻", "http://news.zgw.com/ylxw/"]
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
        for url in response.css(".trends h3 a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        page=response.xpath('//a[text()="下一页"]/@href').get()
        date_list=response.xpath('//*[@class="trends"]/span/text()').getall()
        page_time=date2time(time_str=date_list[-1])
        next_url=f"https://news.zgw.com{page}"
        response.meta['num'] += 1
        yield from over_page(next_url, response, page_time=page_time, page_num=response.meta['num'], callback=self.parse)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text','//*[@class="neirong"]/p//text()|//*[@class="TRS_Editor"]//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="fenxiang"]/p/text()',re='来源：(.*)')  # 来源/article_source
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
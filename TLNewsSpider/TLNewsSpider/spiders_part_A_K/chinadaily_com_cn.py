# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time

from ..utils import date, over_page,date2time
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class ChinadailyComCnSpider(scrapy.Spider):
    name = 'chinadaily.com.cn'
    allowed_domains = ['chinadaily.com.cn']
    site_name = '中国日报网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 财经>跨国公司", "http://caijing.chinadaily.com.cn/5b762029a310030f813cf44f"],
        ["宏观舆情", "首页 > 财经>财经要闻", "http://caijing.chinadaily.com.cn/5b761fc9a310030f813cf44d"],
        ["行业舆情", "首页 > 财经>证券>财经大事", "http://caijing.chinadaily.com.cn/stock/5f646b7fa3101e7ce97253d3"],
        ["行业舆情", "首页 > 财经>金融>头条新闻", "http://finance.chinadaily.com.cn/5b761eb1a310030f813cf43a"],
        ["企业舆情", "首页 > 财经>汽车>行业资讯", "http://che.chinadaily.com.cn/5b7626cda310030f813cf470"],
        ["企业舆情", "首页 > 财经>汽车>汽车要闻", "http://che.chinadaily.com.cn/5b7626cda310030f813cf46c"],
        ["企业舆情", "首页 > 财经>房产>行业资讯", "http://fang.chinadaily.com.cn/5b75426aa310030f813cf41d"]
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
        # 详情页
        for data in response.xpath('//*[@class="busBox3"]/div/div[not(@class)]'):
            data_url=data.xpath('./h3/a/@href').get()
            data_time=data.xpath('./p/b/text()').get()
            url=f"http:{data_url}"
            pagetime=date2time(min_str=data_time)
            yield from over_page(url,response,page_time=pagetime,callback=self.parse_detail)

        # 翻页
        page=response.xpath('//*[@class="next"]/a/@href').get()
        next_url=f"http:{page}"
        yield from over_page(next_url, response, page_time=pagetime, callback=self.parse)


    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        content=response.xpath('//*[@class="article"]/p//text()').getall()
        content_text=[x.strip() for x in content if x.strip() != '']
        item.add_value('content_text',content_text)  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="xinf-le"]/a/text()')  # 来源/article_source
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
        return item.load_item()

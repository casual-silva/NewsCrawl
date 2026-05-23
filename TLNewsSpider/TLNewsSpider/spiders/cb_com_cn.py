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



class CbComCnSpider(scrapy.Spider):
    name = 'cb.com.cn'
    allowed_domains = ['cb.com.cn']
    site_name = '中国经营报'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["宏观舆情", "首页 >宏观经济", "http://www.cb.com.cn/index/list/jj/cv/1"],
        ["企业舆情", "首页 >银行", "http://www.cb.com.cn/index/list/jr/cv/1"],
        ["企业舆情", "首页 >消费", "http://www.cb.com.cn/index/list/gs/cv/9"],
        ["企业舆情", "首页 >能源化工", "http://www.cb.com.cn/index/list/gs/cv/10"],
        ["企业舆情", "首页 >汽车", "http://www.cb.com.cn/index/index/qc"],
        ["企业舆情", "首页 >房地产建材", "http://www.cb.com.cn/index/list/gs/cv/3"],
        ["企业舆情", "首页 >家电家居", "http://www.cb.com.cn/index/list/gs/cv/4"],
        ["企业舆情", "首页 >体育", "http://www.cb.com.cn/index/list/gs/cv/11"],
        ["企业舆情", "首页 >医疗健康", "http://www.cb.com.cn/index/list/gs/cv/7"],
        ["企业舆情", "首页 >文娱", "http://www.cb.com.cn/index/list/gs/cv/8"],
        ["企业舆情", "首页 >科技", "http://www.cb.com.cn/index/list/gs/cv/1"],
        ["企业舆情", "首页 >航旅交运", "http://www.cb.com.cn/index/list/gs/cv/6"]
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
        if 'http://www.cb.com.cn/index/index/qc' == response.url:
            for i in range(0,100):
                url='http://www.cb.com.cn/index/index/videoLoadMore'
                data={'limit':'6','start':str(i),'currentColumnId': '14'}
                yield from over_page(url, response, callback=self.parse_LoadMore, formdata=data,
                                     page_num=i)
                # yield scrapy.FormRequest(url,callback=self.parse_LoadMore,meta=response.meta,formdata=data)

        elif 'index/list' in response.url:
            yield response.follow(response.url, callback=self.parse_index, meta=response.meta,dont_filter=True)

    def parse_index(self, response):
        bar_id=response.xpath('//*[@name="bar_id"]/@value').get()
        for i in range(0, 100):
            url = 'http://www.cb.com.cn/index/index/generalLoadMore'
            data = {'limit': '10','start': str(i),'barId': bar_id,'per_id': ''}
            yield from over_page(url, response, callback=self.parse_LoadMore, formdata=data,
                                 page_num=i)
            # yield scrapy.FormRequest(url, callback=self.parse_LoadMore, meta=response.meta, formdata=data)
    
    def parse_LoadMore(self, response):
        data=json.loads(response.text).get('data')
        datalist=data.get('dataList')
        for d in datalist:
            url=d.get('url')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text', '//*[@class="p_y_20"]/div//p//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="p_x_20"]/div/div[3]/text()',re='来源：(.*)')  # 来源/article_source
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

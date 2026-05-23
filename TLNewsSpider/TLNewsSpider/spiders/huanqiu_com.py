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



class HuanqiuComSpider(scrapy.Spider):
    name = 'huanqiu.com'
    allowed_domains = ['huanqiu.com']
    site_name = '环球网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页>财经>金融", "https://finance.huanqiu.com/jinr"],
        ["行业舆情", "首页>财经>产经", "https://finance.huanqiu.com/chanjing"],
        ["行业舆情", "首页>财经>资本市场", "https://finance.huanqiu.com/captial"],
        ["宏观舆情", "首页>财经>国际财讯", "https://finance.huanqiu.com/international"],
        ["企业舆情", "首页>财经›上市公司", "https://finance.huanqiu.com/ssgs"]
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
        for i in range(0,240,20):
            if 'huanqiu.com/jinr' in response.url:
                jinr_url=f"https://finance.huanqiu.com/api/list2?node=/e3pmh1hmp/e3pn61831&offset={i}&limit=20"
                yield from over_page(jinr_url, response, page_num=i / 20, callback=self.parse_jijing)
            elif'huanqiu.com/chanjing' in response.url:
                chanjing_url=f"https://finance.huanqiu.com/api/list2?node=/e3pmh1hmp/e3pn61chp&offset={i}&limit=20"
                yield from over_page(chanjing_url, response, page_num=i / 20, callback=self.parse_jijing)
            elif 'huanqiu.com/captial' in response.url:
                capital_url=f"https://finance.huanqiu.com/api/list2?node=/e3pmh1hmp/e7i6qafud&offset={i}&limit=20"
                yield from over_page(capital_url, response, page_num=i / 20, callback=self.parse_jijing)
            elif 'huanqiu.com/international' in response.url:
                int_url=f"https://finance.huanqiu.com/api/list2?node=/e3pmh1hmp/e3pmh1iab&offset={i}&limit=20"
                yield from over_page(int_url, response, page_num=i / 20, callback=self.parse_jijing)
            elif 'huanqiu.com/ssgs' in response.url:
                ssgs_url=f"https://finance.huanqiu.com/api/list2?node=/e3pmh1hmp/e3pn62ihu&offset={i}&limit=20"
                yield from over_page(ssgs_url, response, page_num=i / 20, callback=self.parse_jijing)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        list=json.loads(response.text).get('list')
        for li in list:
            aid=li.get('aid')
            url=f"https://finance.huanqiu.com/article/{aid}"
            source=li.get('source')
            name=source.get('name')
            response.meta['source']=name
            ctime=li.get('ctime')
            ctime_=date(ctime)
            pagetime=date2time(time_str=ctime_)
            yield from over_page(url,response,page_num=1,page_time=pagetime,callback=self.parse_detail)
            # yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_value('article_source', response.meta['source'])  # 来源/article_source
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

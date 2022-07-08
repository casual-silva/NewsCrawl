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



class CfbondComSpider(scrapy.Spider):
    name = 'cfbond.com'
    allowed_domains = ['cfbond.com']
    site_name = '中国财富网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["宏观舆情", "首页 > 园区", "http://www.cfbond.com/zgcfw/ejy/yq/list.shtml"],
        ["企业舆情", "首页 > 汽车>资讯", "http://auto.cfbond.com/news/index.html"],
        ["行业舆情", "首页 > 房产", "http://www.cfbond.com/zgcfw/ejy/fc/list.shtml"],
        ["企业舆情", "首页 > 发布易>分发中心", "https://irnews.cfbond.com/index.html"]
    ]
    
    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'zgcfw/ejy/yq/list' in response.url:
            for i in range(1,100):
                url=f"http://www.cfbond.com/zgcfw/ejy/yq/NewsList_{i}.json"
                yield from over_page(url, response, page_num=i, callback=self.parse_yuanqu)
                # yield scrapy.Request(url=url,callback=self.parse_yuanqu,meta=response.meta)
        #
        elif 'news/index' in response.url:
            yield from self.parse_news(response)
            
        elif 'zgcfw/ejy/fc/list' in response.url:
            for i in range(1,100):
                url=f"http://www.cfbond.com/zgcfw/ejy/fc/NewsList_{i}.json"
                yield from over_page(url, response, page_num=i, callback=self.parse_yuanqu)
                # yield scrapy.Request(url=url,callback=self.parse_yuanqu,meta=response.meta)
                
        elif 'irnews.cfbond' in response.url:
            url='https://irnews.cfbond.com/news.json'
            for i in range(1,100):
                data={'ipage': str(i),'categoryid':'', 'origin':''}
                yield from over_page(url, response, callback=self.parse_irnews, formdata=data,
                                     page_num=i)
                # yield scrapy.FormRequest(url,callback=self.parse_irnews,meta=response.meta,formdata=data)

    def parse_yuanqu(self, response):
        info = json.loads(response.text).get('info')
        for inf in info:
            url = inf.get('url')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
    def parse_irnews(self, response):
            obj = json.loads(response.text).get('obj')
            list = obj.get('list')
            for li in list:
                remark=li.get('remark1')
                url = f"https://irnews.cfbond.com/detail.html?newsid={remark}"
                yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    # 首页 - 保险 - 行业公司
    def parse_news(self, response):
        list=response.css(".news_index_left_list_con  ul li a")
        if list != []:
            for url in list:
                yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        else:
            for li in response.css("li a"):
                yield response.follow(li, callback=self.parse_detail, meta=response.meta)
        
    
        # 翻页
        for i in range(2,100):
            url = f"http://auto.cfbond.com/in/news/index_{i}.shtml"
            yield from over_page(url, response, page_num=i, callback=self.parse_news)
            # yield response.follow(url, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="ly"]//text()',re='来源:(.*)')  # 来源/article_source
        item.add_xpath('article_source', '//*[@class="newsDetail_data"]/span[2]/text()', re='来源：(.*)')  # 来源/article_source
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

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



class Big5OcnComCnSpider(scrapy.Spider):
    name = 'big5.ocn.com.cn'
    allowed_domains = ['big5.ocn.com.cn']
    site_name = '中投网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["宏观舆情", "首页>宏观动态>动态", "http://big5.ocn.com.cn/hongguan/hongguanjingji/"],
        ["宏观舆情", "首页>宏观动态>数据", "http://big5.ocn.com.cn/hongguan/hongguanshuju/"],
        ["行业舆情", "首页>产经资讯>医疗健康", "http://big5.ocn.com.cn/chanjing/idynews/2/"],
        ["行业舆情", "首页>产经资讯>装备制造", "http://big5.ocn.com.cn/chanjing/idynews/8/"],
        ["行业舆情", "首页>产经资讯>信息技术", "http://big5.ocn.com.cn/chanjing/idynews/116/"],
        ["行业舆情", "首页>产经资讯>汽车及零部件", "http://big5.ocn.com.cn/chanjing/idynews/82/"],
        ["行业舆情", "首页>产经资讯>文体教育", "http://big5.ocn.com.cn/chanjing/idynews/12/"],
        ["行业舆情", "首页>产经资讯>金融保险", "http://big5.ocn.com.cn/chanjing/idynews/81/"],
        ["行业舆情", "首页>产经资讯>现代服务业", "http://big5.ocn.com.cn/chanjing/idynews/33/"],
        ["行业舆情", "首页>产经资讯>旅游酒店", "http://big5.ocn.com.cn/chanjing/idynews/11/"],
        ["行业舆情", "首页>产业分析>分析", "http://big5.ocn.com.cn/chanye/chanyefenxi/"],
        ["宏观舆情", "首页>行业数据>宏观数据", "http://big5.ocn.com.cn/shujuzhongxin/macroscopic/"],
        ["行业舆情", "首页>行业数据>行业数据", "http://big5.ocn.com.cn/shujuzhongxin/analysedata/"],
        ["地区舆情", "首页>行业数据>城市数据", "http://big5.ocn.com.cn/shujuzhongxin/city/"],
        ["行业舆情", "首页>行业数据>产销数据", "http://big5.ocn.com.cn/shujuzhongxin/production/"],
        ["企业舆情", "首页>行业数据>企业排名", "http://big5.ocn.com.cn/shujuzhongxin/enterprise//"]
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
        for url in response.css("li div.title a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        response.meta['num'] += 1
        page = response.xpath('//a[text()="下一頁"]/@href').get()
        next_url=f"http://big5.ocn.com.cn/{page}"
        yield from over_page(next_url, response, page_num=response.meta['num'], callback=self.parse)


    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        content=response.xpath('//*[@class="cont fontst defSize"]//p//text()').getall()
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

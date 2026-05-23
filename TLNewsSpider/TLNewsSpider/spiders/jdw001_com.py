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



class Jdw001ComSpider(scrapy.Spider):
    name = 'jdw001.com'
    allowed_domains = ['jdw001.com']
    site_name = '第一家电网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页>要闻", "http://www.jdw001.com/portal.php?mod=list&catid=1"],
        ["企业舆情", "首页>黑色家电", "http://www.jdw001.com/portal.php?mod=list&catid=12"],
        ["企业舆情", "首页>白色家电", "http://www.jdw001.com/portal.php?mod=list&catid=13"],
        ["企业舆情", "首页>厨卫电器", "http://www.jdw001.com/portal.php?mod=list&catid=14"],
        ["企业舆情", "首页>小家电", "http://www.jdw001.com/portal.php?mod=list&catid=15"],
        ["企业舆情", "首页>数码通讯", "http://www.jdw001.com/portal.php?mod=list&catid=18"],
        ["企业舆情", "首页>太阳能", "http://www.jdw001.com/portal.php?mod=list&catid=16"],
        ["企业舆情", "首页>空气能", "http://www.jdw001.com/portal.php?mod=list&catid=17"],
        ["企业舆情", "首页>上游部件", "http://www.jdw001.com/portal.php?mod=list&catid=19"]
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
        for url in response.css("dt.xs2 a"):
            response.meta['content']=[]
            yield response.follow(url, callback=self.parse_content, meta=response.meta)

        # 翻页,非标准时间无法限制时间
        page=response.xpath('//a[@class="nxt"]/@href').get()
        response.meta['num'] += 1
        yield from over_page(page, response,page_num=response.meta['num'], callback=self.parse_jijing)
    
    def parse_content(self,response):
        content=response.xpath('//*[@id="article_content"]//text()').getall()
        content_text=''.join(content)
        response.meta['content'].append(content_text)
        next_content=response.xpath('//a[@class="nxt"]/@href').get()
        if next_content != None:
            next_url=f"http://www.jdw001.com/{next_content}"
            yield scrapy.Request(next_url,callback=self.parse_content,meta=response.meta)
        else:
            yield scrapy.Request(response.url,callback=self.parse_detail,meta=response.meta,dont_filter=True)
            
        

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text',response.meta['content'])  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="xg1"]/text()',re='来自: (.*)')  # 来源/article_source
        item.add_xpath('author','//*[@class="xg1"]/text()',re='原作者: (.*)')  # 作者/author
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

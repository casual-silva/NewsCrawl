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



class MeiNetCnSpider(scrapy.Spider):
    name = 'mei.net.cn'
    allowed_domains = ['mei.net.cn']
    site_name = '机经网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页>行业>行业资讯",
         "http://www.mei.net.cn/recommend/more/f2fca9d9-d0c1-4eec-8401-2026eff7f8a4/112211/pages/1.html#!fenye=1"],
        ["企业舆情", "首页>企业>企业动态",
         "http://www.mei.net.cn/recommend/more/3f8becc0-3935-4786-ac8f-eba7ade20087/qydt3414/pages/1.html#!fenye=1"],
        ["宏观舆情", "首页>产经>宏观政策",
         "http://www.mei.net.cn/recommend/more/27b871bc-3d46-4b0b-9304-edb86181cf18/pdfgg222/pages/1.html#!fenye=1"],
        ["宏观舆情", "首页>产经>国家经济",
         "http://www.mei.net.cn/recommend/more/27b871bc-3d46-4b0b-9304-edb86181cf18/dfsfd1231312/pages/1.html#!fenye=1"],
        ["宏观舆情", "首页>产经>区域经济",
         "http://www.mei.net.cn/recommend/more/27b871bc-3d46-4b0b-9304-edb86181cf18/sdsdf112/pages/1.html#!fenye=1"],
        ["宏观舆情", "首页>产经>部位信息",
         "http://www.mei.net.cn/recommend/more/27b871bc-3d46-4b0b-9304-edb86181cf18/sdfsdf222/pages/1.html#!fenye=1"]
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
        #直接在parse里遍历页码的翻页
        if '/f2fca9d9-d0c1-4eec-8401-2026eff7f8a4/112211/' in  response.url:
           yield from self.parse_jijing(response)
           for i in range(2,51):
               url=f"http://www.mei.net.cn/recommend/more/f2fca9d9-d0c1-4eec-8401-2026eff7f8a4/112211/pages/{i}.html#!fenye={i}"
               yield from over_page(url,response,page_num=i-1,callback=self.parse_jijing)
               
        elif '/3f8becc0-3935-4786-ac8f-eba7ade20087/qydt3414/' in  response.url:
           yield from self.parse_jijing(response)
           for i in range(2,101):
               url=f"http://www.mei.net.cn/recommend/more/3f8becc0-3935-4786-ac8f-eba7ade20087/qydt3414/pages/{i}.html#!fenye={i}"
               yield from over_page(url,response,page_num=i-1,callback=self.parse_jijing)
               
        elif '/27b871bc-3d46-4b0b-9304-edb86181cf18/pdfgg222/' in  response.url:
           yield from self.parse_jijing(response)
           
        elif '/27b871bc-3d46-4b0b-9304-edb86181cf18/dfsfd1231312/' in  response.url:
           yield from self.parse_jijing(response)
           
        elif '/27b871bc-3d46-4b0b-9304-edb86181cf18/sdsdf112/' in  response.url:
           yield from self.parse_jijing(response)
           for i in range(2,21):
               url=f"http://www.mei.net.cn/recommend/more/27b871bc-3d46-4b0b-9304-edb86181cf18/sdsdf112/pages/{i}.html#!fenye={i}"
               yield from over_page(url,response,page_num=i-1,callback=self.parse_jijing)
               
        elif '/27b871bc-3d46-4b0b-9304-edb86181cf18/sdfsdf222/' in  response.url:
           yield from self.parse_jijing(response)



    # 下一页的翻页方式
    def parse_jijing(self, response):
        for data in response.xpath('//*[@name="infoListTr"]'):
            url_data=data.xpath('./h3/a/@href').get()
            time_data=data.xpath('./div[@class="item-type"]/em/text()').get()
            url=f"http://www.mei.net.cn{url_data}"
            pagetime=date2time(min_str=time_data)
            yield from over_page(url,response,page_num=1,page_time=pagetime,callback=self.parse_detail)


    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text', '//*[@id="divContent"]/p[not(@style)]//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="create_time"]/a/text()')  # 来源/article_source
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

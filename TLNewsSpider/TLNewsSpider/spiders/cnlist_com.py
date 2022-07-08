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



class CnlistComSpider(scrapy.Spider):
    name = 'cnlist.com'
    allowed_domains = ['cnlist.com']
    site_name = '中国上市公司资讯网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "新闻首页 > 公司新闻 > 沪深主板",
         "http://www.cnlist.com/information/newsSplitList.jsp?url=/getCompanyNewsList.do&typeCode=gsxw&columnCode=shzb"],
        ["企业舆情", "新闻首页 > 公司新闻 > 创业板",
         "http://www.cnlist.com/information/newsSplitList.jsp?url=/getCompanyNewsList.do&typeCode=gsxw&columnCode=cyb"],
        ["企业舆情", "新闻首页 > 公司新闻 > 新三板",
         "http://www.cnlist.com/information/newsSplitList.jsp?url=/getCompanyNewsList.do&typeCode=gsxw&columnCode=xsb"]
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
        if 'columnCode=shzb' in response.url:
            for i in range(1,101):
                url=f"http://www.cnlist.com/information/newsSplitList.jsp?pageNo={i}&pageSize=18&pageName=splitList&columnCode=shzb&typeCode=gsxw&split=true&pageURL=%2Finformation%2FnewsSplitList&url=%2FgetCompanyNewsList.do"
                yield from over_page(url, response, callback=self.parse_cnlist,
                                     page_num=i)
                # yield scrapy.Request(url,callback=self.parse_cnlist,meta=response.meta)

        elif 'columnCode=cyb' in response.url:
            for i in range(1, 101):
                url = f"http://www.cnlist.com/information/newsSplitList.jsp?pageNo={i}&pageSize=18&pageName=splitList&columnCode=cyb&typeCode=gsxw&split=true&pageURL=%2Finformation%2FnewsSplitList&url=%2FgetCompanyNewsList.do"
                yield from over_page(url, response, callback=self.parse_cnlist,
                                     page_num=i)
                # yield scrapy.Request(url, callback=self.parse_cnlist, meta=response.meta)
                
        elif 'columnCode=xsb' in response.url:
            for i in range(1,101):
                url=f"http://www.cnlist.com/information/newsSplitList.jsp?pageNo={i}&pageSize=18&pageName=splitList&columnCode=xsb&typeCode=gsxw&split=true&pageURL=%2Finformation%2FnewsSplitList&url=%2FgetCompanyNewsList.do"
                yield from over_page(url, response, callback=self.parse_cnlist,
                                     page_num=i)
                # yield scrapy.Request(url,callback=self.parse_cnlist,meta=response.meta)

    # 首页>基金
    def parse_cnlist(self, response):
        
        for onc in response.xpath('//*[@class="list_data"]/ul/li'):
            onclick=onc.xpath('./a/@onclick').get()
            pd=onc.xpath('.//span[@class="date"]/text()').get()
            code=re.findall('[1-9][0-9]*',str(onclick))
            code_=''.join(code)
            url=f"http://www.cnlist.com/information/newsContent.jsp?id={code_}"
            response.meta['pd']=pd
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date',response.meta['pd'])  # 发布日期/publish_date
        content=response.xpath('//*[@id="confon"]//text()').getall()
        content_text=[x.strip() for x in content if x.strip() != '']
        item.add_value('content_text',content_text)  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="list_content_details"]/span/text()',re='来源：(.*)\xa0')  # 来源/article_source
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

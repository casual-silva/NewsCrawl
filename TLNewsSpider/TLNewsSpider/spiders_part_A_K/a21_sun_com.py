# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit

from ..utils import date, over_page,date2time
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class A21SunComSpider(scrapy.Spider):
    name = '21-sun.com'
    allowed_domains = ['21-sun.com']
    site_name = '中国工程机械商贸网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 企业", "http://news.21-sun.com/list/qiye_1_1.htm"],
        ["企业舆情", "中国工程机械商贸网 > 资讯中心", "http://news.21-sun.com"]
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
        if 'qiye_1_1.htm' in  response.url:
            yield from self.parse_jijing(response)
            for i in range(3,201):
               num=i-2
               url=f"https://news.21-sun.com/information_list_2020/action/ajax.jsp?flag=getMoreSolr&nowPage={i}&pageSize=10&class_id=1"
               yield from over_page(url,response,page_num=num,callback=self.parse_jijing)
            #
        else:
            yield from self.parse_qiye(response)
            for i in range(3, 51):
                num=i-2
                url = f"https://news.21-sun.com/information_list_2020/action/ajax.jsp?flag=getMoreNew&nowPage={i}&pageSize=10"
                yield from over_page(url, response, page_num=num, callback=self.parse_qiye)

    def parse_jijing(self, response):
        for data in response.xpath('//*[@class="con_info l"]'):
            data_url=data.xpath('./a[1]/@href').get()
            url=f"https://news.21-sun.com{data_url}"
            data_time=data.xpath('.//p[@class="words l"]/text()').get()
            pagetime=date2time(date_str=data_time)
            yield from over_page(url,response,page_num=1,page_time=pagetime,callback=self.parse_detail)
            
    def parse_qiye(self,response):
        for data in response.xpath('//*[@class="con_info l"]'):
            data_url=data.xpath('./a[1]/@href').get()
            data_time=data.xpath('.//p[@class="words l"]/text()').get()
            pagetime=date2time(date_str=data_time)
            yield from over_page(data_url,response,page_num=1,page_time=pagetime,callback=self.parse_detail)


    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title', '//*[@class="news_content"]/div[@class="tit"]/text() ')  # 标题/title
        pd=self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('/','-')
        item.add_value('publish_date', publish_date)  # 发布日期/publish_date
        item.add_xpath('content_text', '//*[@class="content"]/p[not(@class)]//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="reprint"]/text()',re='转载自(.*)，')  # 来源/article_source
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
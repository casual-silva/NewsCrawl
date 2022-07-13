# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit

from ..utils import date, over_page,date2time
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class BjxComCnSpider(scrapy.Spider):
    name = 'bjx.com.cn'
    allowed_domains = ['bjx.com.cn']
    site_name = '北极星电力新闻网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "电力 > 电力新闻网 >  企业", "https://news.bjx.com.cn/mq"],
        ["企业舆情", "电力 > 电力新闻网 >  要闻", "https://news.bjx.com.cn/list"]
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
        for data in response.xpath('//*[@class="cc-list-content"]/ul/li'):
            data_url=data.xpath('./a/@href').get()
            data_time=data.xpath('./span/text()').get()
            pagetime=date2time(date_str=data_time)
            yield from over_page(data_url,response,page_time=pagetime,callback=self.parse_detail)

        # 翻页
        page=response.xpath('//a[text()="下一页"]/@href').get()
        next_url=f"https://news.bjx.com.cn{page}"
        yield from over_page(next_url, response, page_time=pagetime, callback=self.parse)


    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        pd=self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('/','-')
        item.add_value('publish_date',publish_date )  # 发布日期/publish_date
        content=response.xpath('//*[@class="list_detail"]/p//text()').getall()
        content_=response.xpath('//*[@class="hydetail_content"]/div[not(@class)]/p//text()').getall()
        if content==[] and content_ != []:
            content_text=[x.strip() for x in content_ if x.strip() != '']
        elif content_==[] and content!= []:
            content_text = [x.strip() for x in content if x.strip() != '']
        else:
            content_text=content_rules.extract(response.text)
        item.add_value('content_text',content_text)  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="list_copy"]/b/text()',re='来源:(.*)')  # 来源/article_source
        item.add_xpath('article_source', '//*[@class="hydetail_tit"]/h5/a[2]/text()')  # 来源/article_source
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
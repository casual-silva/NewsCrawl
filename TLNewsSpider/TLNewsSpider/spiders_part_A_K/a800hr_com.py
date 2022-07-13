# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time

from ..utils import date,over_page,date2time,pubdate_common
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor


class A800hrComSpider(scrapy.Spider):
    name = '800hr.com'
    site_name = '英才网联'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()
    allowed_domains = ['news.buildhr.com', 'news.healthr.com', '800hr.com', 'news.bankhr.com','news.michr.com','news.chenhr.com']
    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 行业资讯 > 建筑行业资讯", "https://news.buildhr.com/more.php?type=144"],
        ["行业舆情", "首页 > 行业资讯 > 金融行业资讯", "https://news.bankhr.com/more.php?type=596"],
        ["企业舆情", "首页 > 行业资讯 > 医药行业资讯", "https://news.healthr.com/more.php?type=45"],
        ["行业舆情", "首页 > 行业资讯 > 制造行业资讯", "https://news.michr.com/more.php?type=27"],
        ["行业舆情", "首页 > 行业资讯 > 化工行业资讯", "https://news.chenhr.com/more.php?type=56"]
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
        for html in response.xpath('//*[@class="morenews"]/ul/li'):
            html_url= html.xpath('./h2/a/@href').get()
            url=f"https:{html_url}"
            source = html.xpath('./h1//address/text()').get()
            source_ = re.findall('发布：(.*)', source)
            html_time=html.xpath('./h1/span/b/text()').get()
            html_time_=pubdate_common.handle_pubdate(pubdate_str=html_time)
            pagetime=date2time(date_str=html_time_.strip())
            response.meta['article_source'] = source_
            response.meta['content_list']=[]
            yield from over_page(url,response,page_time=pagetime,callback=self.parse_next)
    
        # 翻页
        page=response.xpath('//a[text()="下一页"]/@href').get()
        yield from over_page(page, response, page_time=pagetime, callback=self.parse)
           
    
    def parse_next(self, response):
        content_next = response.xpath('//a[text()="下一页"]/@href').get()
        if content_next == None or 'java' in content_next:
            content_ = response.xpath('//*[@class="newsContent"]//p//text()').getall()
            content_text = ''.join(content_)
            response.meta['content_list'].append(content_text)
            yield from self.parse_detail(response)
        else:
            content_ = response.xpath('//*[@class="newsContent"]//p//text()').getall()
            content_text = ''.join(content_)
            response.meta['content_list'].append(content_text)
            next_url=f"https://news.bankhr.com/{content_next}"
            yield scrapy.Request(url=next_url,callback=self.parse_next,meta=response.meta)
    #
    
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        pd= self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('年','-').replace('月','-').replace('日','')
        item.add_value('publish_date',publish_date)  # 发布日期/publish_date
        item.add_value('content_text', response.meta['content_list'])  # 正文内容/text_content
        
        # 自定义规则
        item.add_value('article_source', response.meta['article_source'])  # 来源/article_source
        item.add_value('author', self.author_rules.extractor(response.text))  # 作者/author
        # 默认保存一般无需更改
        item.add_value('spider_time', date())  # 抓取时间
        item.add_value('created_time', date())  # 更新时间
        item.add_value('source_url', response.url)  # 详情网址/detail_url
        item.add_value('site_name', self.site_name)  # 站点名称
        item.add_value('site_url', urlsplit(response.url).netloc)  # 站点host
        item.add_value('classification', response.meta['classification'])  # 所属分类
        # 网页源码  调试阶段注释方便查看日志
        item.add_value('html_text', response.text)  # 网页源码
        yield item.load_item()
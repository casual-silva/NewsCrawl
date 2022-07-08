# -*- coding: utf-8 -*-

import re

import scrapy
from urllib.parse import urlsplit

from ..utils import date, over_page
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor
from lxml import etree


class CfachinaOrgSpider(scrapy.Spider):
    name = 'cfachina.org'
    allowed_domains = ['cfachina.org']
    site_name = '中国期货业协会'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页>行业动态>行业要闻", "http://www.cfachina.org/industrydynamics/industrynews/"]
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
        for i in range(1,57):
            url=f"http://www.cfachina.org//qx-search/api/wcmSearch/searchDocsByProgram?pageNo={i}&pageSize=15&keyword=&programName=%E8%A1%8C%E4%B8%9A%E8%A6%81%E9%97%BB"
            yield from over_page(url, response, page_num=i, callback=self.parse_cfachina)
            # yield response.follow(url, callback=self.parse_cfachina, meta=response.meta)
   
    # 首页>基金
    def parse_cfachina(self, response):
        dataList=re.findall('<docId>([\s\S]*?)<wcmappendixVOList/>',response.text)
        for d in dataList:
            docTitle=re.findall('<docTitle>(.*)</docTitle>',d)
            docSourceName=re.findall('<docSourceName>(.*)</docSourceName>',d)
            docContent = re.findall('<docContent>([\s\S]*)</docContent>',d)
            operTime = re.findall('<operTime>(.*)</operTime>',d)
            docPubUrl = re.findall('<docPubUrl>(.*)</docPubUrl>',d)
            response.meta['title']=''.join(docTitle)
            response.meta['publish_date']= ''.join(operTime)
            response.meta['content_text']= ''.join(docContent)
            response.meta['article_source'] = ''.join(docSourceName)
            url = ''.join(docPubUrl)
            response.meta['source_url']=f"http://www.cfachina.org{url}"
            yield from self.parse_detail(response)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)

        item.add_value('title', response.meta['title'])  # 标题/title
        item.add_value('publish_date', response.meta['publish_date'])  # 发布日期/publish_date
        item.add_value('content_text',response.meta['content_text'])  # 正文内容/text_content
        item.add_value('article_source',response.meta['article_source'])  # 来源/article_source
        item.add_value('author',self.author_rules.extractor(response.text))  # 作者/author
        item.add_value('spider_time', date())  # 抓取时间
        item.add_value('created_time', date())  # 更新时间
        item.add_value('source_url',response.meta['source_url'])  # 详情网址/detail_url
        item.add_value('site_name', self.site_name)  # 站点名称
        item.add_value('site_url', urlsplit(response.url).netloc)  # 站点host
        item.add_value('classification', response.meta['classification'])  # 所属分类
        # 网页源码  调试阶段注释方便查看日志
        # 该数据在接口获取所以源码是接口的xml源码
        item.add_value('html_text', response.text)  # 网页源码
        #因为在for循环中返回所以改用yield
        yield item.load_item()

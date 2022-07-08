# -*- coding: utf-8 -*-
import json
import re
import math
import scrapy
from urllib.parse import urlsplit
from lxml import etree
from ..utils import date, over_page
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class PowerpigsNetSpider(scrapy.Spider):
    name = 'powerpigs.net'
    allowed_domains = ['powerpigs.net']
    site_name = '猪场动力网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 资讯", "https://www.powerpigs.net/index.php?2"]
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
        #post请求的遍历页码的翻
        for i in range(1,100):
            url='https://powerpigs.net/2f0643b2/information/getInformation'
            data={'typeId': '-1', 'page': str(i),'size': '8'}
            response.meta['num'] +=1
            yield from over_page(url,response,callback=self.parse_jijing,body=json.dumps(data),page_num=response.meta['num'])

    # 下一页的翻页方式
    def parse_jijing(self, response):
        data=json.loads(response.text).get('data')
        data_page=data.get('data')
        for d in data_page:
            informationId=d.get('informationId')
            page_url=f"https://www.powerpigs.net/index.php?3&{informationId}"
            response.meta['source_url']=page_url
            url='https://powerpigs.net/2f0643b2/information/getDetail'
            data={'informationId': informationId}
            yield scrapy.Request(url,callback=self.parse_detail,method='POST',body=json.dumps(data),meta=response.meta)
    
    def parse_detail(self, response):
        data=json.loads(response.text).get('data')
        author=data.get('author')
        informationAtime=data.get('informationAtime')
        informationTitle=data.get('informationTitle')
        informationContent=data.get('informationContent')
        html=etree.HTML(informationContent)
        content = html.xpath('//text()')
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        item.add_value('title', informationTitle)  # 标题/title
        item.add_value('publish_date', informationAtime)  # 发布日期/publish_date
        content_text=[x.strip() for x in content if x.strip() != '']
        item.add_value('content_text', content_text)  # 正文内容/text_content
        # 自定义规则
        item.add_value('article_source',content_text, re='来源：(.*)')  # 来源/article_source
        item.add_value('author',author)  # 作者/author
        # 默认保存一般无需更改
        item.add_value('spider_time', date())  # 抓取时间
        item.add_value('created_time', date())  # 更新时间
        item.add_value('source_url',response.meta['source_url'])  # 详情网址/detail_url
        item.add_value('site_name', self.site_name)  # 站点名称
        item.add_value('site_url', urlsplit(response.url).netloc)  # 站点host
        item.add_value('classification', response.meta['classification'])  # 所属分类
        # 网页源码  调试阶段注释方便查看日志
        item.add_value('html_text', response.text)  # 网页源码

        # 上面获取值可能为空, 追加匹配值
        # item.add_xpath('title', '//h1/text() || //p/h5/text()', re='[标题]{2}:(.*?)')  # 标题/title
        # item.add_css('publish_date', 'p:nth-last-child(-n+5)', re="[0-9]{0,4}年[0-9]{1,2}月[0-9]{1,2}日")  # 发布日期/publish_date
        return item.load_item()

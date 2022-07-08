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



class CcmnCnSpider(scrapy.Spider):
    name = 'ccmn.cn'
    allowed_domains = ['ccmn.cn']
    site_name = '长江有色金属网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "长江有色金属网 > 资讯首页 > 数据统计", "https://www.ccmn.cn/sjtj/"],
        ["企业舆情", "长江有色金属网 > 资讯首页 > 行业要闻", "https://www.ccmn.cn/hyyw/"]
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
        #post请求的遍历页码的翻页
        if 'ccmn.cn/sjtj/' in  response.url:
            for i in range(0,201):
                url='https://www.ccmn.cn/shop/news/list'
                data={'colName': 'sjtj','pageNo':str(i)}
                yield from over_page(url,response,callback=self.parse_jijing,formdata=data,page_num=i)
                
        elif 'ccmn.cn/hyyw/' in  response.url:
            for i in range(0,501):
                url='https://www.ccmn.cn/shop/news/list'
                data={'colName': 'hyyw','pageNo':str(i)}
                yield from over_page(url,response,callback=self.parse_jijing,formdata=data,page_num=i)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        data=json.loads(response.text).get('data')
        rows=data.get('rows')
        for r in rows:
            htmlUrl=r.get('htmlUrl')
            publishDate=r.get('publishDate')
            url=f"https://www.ccmn.cn/{htmlUrl}"

            pd=date2time(time_str=publishDate)
            yield from over_page(url, response, page_time=pd, page_num=1,
                                 callback=self.parse_detail)
        
            
            

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="left"]/label[2]/text()',re='(.*)\r\n') # 来源/article_source
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

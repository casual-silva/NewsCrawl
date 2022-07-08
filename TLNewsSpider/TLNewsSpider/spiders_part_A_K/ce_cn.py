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



class CeCnSpider(scrapy.Spider):
    name = 'ce.cn'
    allowed_domains = ['ce.cn']
    site_name = '中国经济网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页>产经>公司观察", "http://www.ce.cn/cysc/newmain/pplm/qyxx/"],
        ["行业舆情", "首页>产经>食品>食品行业动态", "http://www.ce.cn/cysc/sp/info/"],
        ["行业舆情", "首页>产经>食品>酒业", "http://www.ce.cn/cysc/sp/jiu/"],
        ["行业舆情", "首页>产经>食品>保健食品", "http://www.ce.cn/cysc/sp/bk/"],
        ["行业舆情", "首页>产经>食品>乳业", "http://www.ce.cn/cysc/sp/ry/"],
        ["行业舆情", "首页>产经>食品>饮料", "http://www.ce.cn/cysc/sp/cy/"],
        ["行业舆情", "首页>产经>食品>餐饮", "http://www.ce.cn/cysc/sp/cyaq/"],
        ["行业舆情", "首页>产经>房产>房产资讯", "http://www.ce.cn/cysc/fdc/fc/"],
        ["行业舆情", "首页>产经>能源>能源资讯", "http://www.ce.cn/cysc/ny/gdxw/"],
        ["行业舆情", "首页>产经>IT", "http://www.ce.cn/cysc/tech/gd2012/"],
        ["行业舆情", "首页>产经>家电>行业新闻", "http://www.ce.cn/cysc/zgjd/hyfx/"],
        ["行业舆情", "首页>产经>交通>铁路", "http://www.ce.cn/cysc/jtys/tielu/"],
        ["行业舆情", "首页>产经>交通>航空", "http://www.ce.cn/cysc/jtys/hangkong/"],
        ["行业舆情", "首页>产经>交通>公路", "http://www.ce.cn/cysc/jtys/gonglu/"],
        ["行业舆情", "首页>产经>交通>海运", "http://www.ce.cn/cysc/jtys/haiyun/"],
        ["行业舆情", "首页>产经>交通>城市交通", "http://www.ce.cn/cysc/jtys/csjt/"],
        ["行业舆情", "首页>产经>交通>综合物流", "http://www.ce.cn/cysc/jtys/zhwl/"],
        ["行业舆情", "首页>产经>交通>交通法规", "http://www.ce.cn/cysc/jtys/fgjd/"],
        ["行业舆情", "首页>产经>医药>行业动态", "http://www.ce.cn/cysc/yy/hydt/"],
        ["行业舆情", "首页>产经>生态>生态保护", "http://www.ce.cn/cysc/stwm/zxdt/"],
        ["行业舆情", "首页>产经>生态>污染防治", "http://www.ce.cn/cysc/stwm/wrfz/"],
        ["行业舆情", "首页>产经>旅游>产业经济", "http://travel.ce.cn/xsy/cy/"],
        ["行业舆情", "首页>产经>文化>文化要闻", "http://www.ce.cn/culture/whcyk/yaowen/"]
    ]
    
    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification,'url':url,'num':0}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'cysc/fdc/fc' in response.url:
            yield from self.parse_fc(response)
        #
        elif 'cysc/yy/hydt'  in response.url:
            yield from self.parse_hydt(response)
            
        elif  'culture/whcyk/yaowen/' in response.url:
            yield from self.parse_hydt(response)
        
        else:
            yield from self.parse_normal(response)

            
    def parse_normal(self, response):
        for url in response.css(".left li a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        response.meta['num']+=1
        page = f"{response.meta['url']}index_{response.meta['num']}.shtml"
        yield from over_page(page, response, page_num=response.meta['num'], callback=self.parse_normal)

    def parse_fc(self, response):
        for url in response.xpath(".sec_left .con li a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        response.meta['num']+=1
        page=f"{response.meta['url']}index_{response.meta['num']}.shtml"
        yield from over_page(page, response, page_num=response.meta['num'], callback=self.parse_fc)

    # 首页 - 保险 - 行业公司
    def parse_hydt(self, response):
        for url in response.xpath('//*[@align="left"]/a'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
        # 翻页
        response.meta['num']+=1
        page = f"{response.meta['url']}index_{response.meta['num']}.shtml"
        yield from over_page(page, response, page_num=response.meta['num'], callback=self.parse_hydt)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@id="articleSource"]/text()',re='来源：(.*)')  # 来源/article_source
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

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



class GscnComCnSpider(scrapy.Spider):
    name = 'gscn.com.cn'
    allowed_domains = ['gscn.com.cn']
    site_name = '中国甘肃网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "中国甘肃网  >  财经  >  金融", "http://finance.gscn.com.cn/sxy/index.html"],
        ["宏观舆情", "中国甘肃网  >  财经  >  产经", "http://finance.gscn.com.cn/tzbd/index.html"],
        ["宏观舆情", "中国甘肃网  >  财经  >  国内财经", "http://finance.gscn.com.cn/cjjd/index.html"],
        ["宏观舆情", "中国甘肃网  >  财经  >  国际财经", "http://finance.gscn.com.cn/qqzx/index.html"],
        ["地区舆情", "中国甘肃网  >  财经  >  省内经济", "http://finance.gscn.com.cn/sljj/index.html"],
        ["企业舆情", "中国甘肃网  >  财经 >  财经锐评", "http://finance.gscn.com.cn/cjpl/index.html"],
        ["地区舆情", "中国甘肃网  >  房产  >  省内要闻", "http://house.gscn.com.cn/fcyw/"],
        ["行业舆情", "中国甘肃网  >  房产  >  国内要闻", "http://house.gscn.com.cn/gnyw/"]
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
        js_html=response.xpath('//*[@id="content"]/script/@src').get()
        if '/sljj/index.html' in response.url:
            response.meta['code']='http://finance.gscn.com.cn/system/count//0018005/000000000000/000/000/c0018005000000000000_000000'
            response.meta['num']=10
            yield scrapy.Request(js_html,callback=self.parse_page,meta=response.meta)
            
        elif 'com.cn/fcyw/' in response.url:
            response.meta['code'] ='http://house.gscn.com.cn/system/count//0022001/000000000000/000/000/c0022001000000000000_000000'
            response.meta['num'] = 3
            yield scrapy.Request(js_html,callback=self.parse_page,meta=response.meta)
            
        elif 'com.cn/gnyw/' in response.url:
            response.meta['num'] = 3
            response.meta['code'] ='http://house.gscn.com.cn/system/count//0022031/000000000000/000/000/c0022031000000000000_000000'
            yield scrapy.Request(js_html,callback=self.parse_page,meta=response.meta)
        
        else:
            yield from self.parse_jijing(response)
            
    def parse_page(self,response):
        maxpage=re.findall('var maxpage = (.*);',response.text)
        mp=''.join(maxpage)
        mp_int=int(mp)
        mp_limit=mp_int-response.meta['num']
        for i in range(mp_limit,mp_int+1):
            next_url=f"{response.meta['code']}{i}.shtml"
            yield scrapy.Request(next_url,meta=response.meta,callback=self.parse_jijing)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        for data in response.xpath('//*[@id="content"]/ul/li'):
            data_url=data.xpath('./a/@href').get()
            data_time=data.xpath('./span/text()').get()
            dt=data_time.replace('/','-')
            pagetime=date2time(date_str=dt)
            yield from over_page(data_url,response,page_num=1,page_time=pagetime,callback=self.parse_detail)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text','//*[@class="a-container"]/p//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="info"]/span/text()',re='来源：(.*)')  # 来源/article_source
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

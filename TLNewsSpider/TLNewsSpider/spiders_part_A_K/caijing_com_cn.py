# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit

from ..utils import date, over_page
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor


class CaijingComCnSpider(scrapy.Spider):
    name = 'caijing.com.cn'
    allowed_domains = ['caijing.com']
    site_name = '财经网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()
    
    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ['企业舆情', '首页 > 企业动态', 'http://www.caijing.com.cn/original/'],
        ['宏观舆情', '首页 > 宏观', 'http://economy.caijing.com.cn/index.html'],
        ['企业舆情', '首页 > 财经', 'http://industry.caijing.com.cn/'],
        ['企业舆情', '首页 > 科技', 'http://tech.caijing.com.cn/'],
        ['企业舆情', '首页 > 地产>公司', 'https://estate.caijing.com.cn/company/'],
        ['行业舆情', '首页 > 地产>行业', 'https://estate.caijing.com.cn/policy/'],
        ['企业舆情', '首页 > 上市公司', 'http://stock.caijing.com.cn/companystock/'],
        ['企业舆情', '首页 >汽车> 资讯', 'http://auto.caijing.com.cn/jsx/zx/'],
        ['企业舆情', '首页 >汽车> 新能源', 'https://auto.caijing.com.cn/jsx/xny/'],
        ['企业舆情', '首页 >汽车>  用车', 'https://auto.caijing.com.cn/jsx/yc/'],
        ['企业舆情', '首页 >汽车> 评测', 'https://auto.caijing.com.cn/jsx/pc/'],
        ['企业舆情', '首页 >汽车> 新车上市', 'https://auto.caijing.com.cn/jsx/xcss/'],
        ['企业舆情', '首页 >汽车> 经销商', 'https://auto.caijing.com.cn/jsx/jxs/'],
        ['企业舆情', '首页>地产 > 公司', 'https://estate.caijing.com.cn/company/'],
        ['行业舆情', '首页>地产 > 行业', 'https://estate.caijing.com.cn/policy/']
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
        if 'www.caijing.com' in response.url:
            yield from self.parse_jijing(response)

        elif 'economy.caijing.com'  in response.url:
            yield from self.parse_baoxian(response)
        
        elif 'industry.caijing.com.cn' in response.url:
            yield from self.parse_baoxian(response)
        
        elif 'tech.caijing.com'  in response.url:
            yield from self.parse_baoxian(response)
            
        elif 'stock.caijing.com.cn' in response.url:
            yield from self.parse_baoxian(response)
            
        elif 'estate.caijing.com.cn' in response.url:
            response.meta['num']= 0
            yield from self.parse_estate(response)
        
        elif 'auto.caijing.com.cn' in response.url:
            response.meta['num'] = 0
            yield from self.parse_auto(response)
    
    # 首页>基金
    def parse_jijing(self, response):
        for url in response.css(".wzbt a "):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
    # 首页 - 保险 - 行业公司
    def parse_baoxian(self, response):
        for url in response.css(".ls_news div a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
    def parse_estate(self, response):
        for url in response.css(".news_lt a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        response.meta['num'] += 1
        page = response.xpath('//a[@class="next"]/@href').get()
        next_url=f"https://estate.caijing.com.cn{page}"
        yield from over_page(next_url, response, page_num=response.meta['num'], callback=self.parse_estate)

    def parse_auto(self, response):
        for url in response.xpath('//*[@class="ls_news_r"]/a'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        page=response.xpath('//a[@class="next"]/@href').get()
        response.meta['num'] += 1
        yield from over_page(page,response,page_num=response.meta['num'],callback=self.parse_auto)
        



    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//span[@id="source_baidu"]/a/text()')
        item.add_xpath('article_source', '//*[@class="source"]/span/text()')
        item.add_xpath('article_source', '//*[@class="news_name"]/a/text()')
        item.add_xpath('article_source', '//*[@class="news_name"][1]/text()')
        item.add_xpath('article_source', '//*[@class="news_frome"]/text()')# 来源/article_source
        item.add_xpath('author', '//*[@id="editor_baidu"]/text()')  # 作者/author
        item.add_xpath('author', '//*[@class="news_name"][2]/text()')
        item.add_xpath('author', '//*[@class="sub"]/a/text()')
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

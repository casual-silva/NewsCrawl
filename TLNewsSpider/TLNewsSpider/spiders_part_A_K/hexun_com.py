# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit

from ..utils import date,over_page,date2time,pubdate_common
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor
import json


class HexunComSpider(scrapy.Spider):
    name = 'hexun.com'
    allowed_domains = ['hexun.com']
    site_name = '和讯网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ['企业舆情', '首页 > 科技', 'http://tech.hexun.com'],
        ['企业舆情', '首页 > 股票>行业 > 行业动态', 'http://stock.hexun.com/dongtai/'],
        ['企业舆情', '首页 > 股票> 港股 > 公司新闻', 'http://stock.hexun.com/hknews/index.html'],
        ['行业舆情', '首页 > 信托 > 信托要闻', 'http://trust.hexun.com/xtyw/index.html'],
        ['行业舆情', '首页 > 信托 > 信托公司新闻', 'http://trust.hexun.com/trust_company/index.html'],
        ['企业舆情', '首页 > 股票 > 上市公司', 'http://stock.hexun.com/gsxw/'],
        ['企业舆情', '首页 > 港股', 'http://hk.stock.hexun.com/'],
        ['企业舆情', '首页 > 公司新闻', 'http://news.hexun.com/listedcompany/'],
        ['行业舆情', '首页 > 房产 > 深度', 'http://house.hexun.com/fcyw/index.html'],
        ['行业舆情', '首页  > 房产 > 房产新闻 > 房产要闻', 'http://house.hexun.com/list/'],
        ['行业舆情', '首页 > 房产 > 房地产金融', 'http://house.hexun.com/fqyw/'],
        ['行业舆情', '首页 > 房产 > 家居要闻', 'http://house.hexun.com/jjyw/index.html'],
        ['行业舆情', '和讯网 > 信托 > 信托行业动态', 'http://trust.hexun.com/trust_industry/index.html']
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
        if 'tech.hexun' in response.url:
            yield from self.parse_tech(response)
            
        elif 'hk.stock.hexun' in response.url:
            yield from self.parse_hk(response)

        elif 'http://trust.hexun.com/xtyw/index.html' == response.url:
            yield from self.parse_xtyw(response)
            
        elif 'http://trust.hexun.com/trust_company/index.html' == response.url:
            yield from self.parse_xtyw(response)

        elif 'http://stock.hexun.com/dongtai/' == response.url:
            for i in range(1,6):
                url_ajax=f"http://open.tool.hexun.com/MongodbNewsService/newsListPageByJson.jsp?id=100235838&s=30&cp={i}&priority=0&callback=hx_json21639988205707"
                yield from over_page(url_ajax,response,page_num=i,callback=self.parse_stock)
        
        elif 'http://stock.hexun.com/hknews/index.html' == response.url:
            for i in range(101):
                url_ajax=f"http://open.tool.hexun.com/MongodbNewsService/newsListPageByJson.jsp?id=100235863&s=70&cp={i}&priority=0&callback=hx_json21639998837144"
                yield from over_page(url_ajax, response, page_num=i, callback=self.parse_stock)
                
        elif 'http://stock.hexun.com/gsxw/' == response.url:
            for i in range(101):
                url_ajax=f"http://open.tool.hexun.com/MongodbNewsService/newsListPageByJson.jsp?id=100235849&s=30&cp={i}&priority=0&callback=hx_json21639998960048"
                yield from over_page(url_ajax,response,page_num=i,callback=self.parse_stock)
                
        elif 'http://news.hexun.com/listedcompany/' == response.url:
            for i in range(101):
                url_ajax=f"https://opentool.hexun.com/MongodbNewsService/newsListPageByJson.jsp?id=108511812&s=30&cp={i}&priority=0&callback=hx_json21639999106768"
                yield from over_page(url_ajax,response,page_num=i,callback=self.parse_stock)
        
        elif 'http://house.hexun.com/fcyw/index.html' == response.url:
            for i in range(101):
                url_ajax=f"http://open.tool.hexun.com/MongodbNewsService/newsListPageByJson.jsp?id=149394322&s=50&cp={i}&priority=0&callback=hx_json21639999158207"
                yield from over_page(url_ajax,response,page_num=i,callback=self.parse_stock)
                
        elif 'http://house.hexun.com/list/' == response.url:
            for i in range(101):
                url_ajax=f"http://open.tool.hexun.com/MongodbNewsService/newsListPageByJson.jsp?id=100135470&s=50&cp={i}&priority=0&callback=hx_json21639999210649"
                yield from over_page(url_ajax,response,page_num=i,callback=self.parse_stock)
                
        elif 'http://house.hexun.com/fqyw/' == response.url:
            for i in range(101):
                url_ajax=f"http://open.tool.hexun.com/MongodbNewsService/newsListPageByJson.jsp?id=123211837&s=50&cp={i}&priority=0&callback=hx_json21639999257215"
                yield from over_page(url_ajax,response,page_num=i,callback=self.parse_stock)
        
        elif 'http://house.hexun.com/jjyw/index.html' == response.url:
            for i in range(101):
                url_ajax=f"http://open.tool.hexun.com/MongodbNewsService/newsListPageByJson.jsp?id=195795098&s=50&cp={i}&priority=0&callback=hx_json21639999346960"
                yield from over_page(url_ajax,response,page_num=i,callback=self.parse_stock)
        
        elif 'http://trust.hexun.com/trust_industry/index.html' == response.url:
            url_ajax=f"https://opentool.hexun.com/MongodbNewsService/newsListPageByJson.jsp?id=125800350&s=30&cp={1}&priority=0&callback=hx_json11639999430754"
            yield from over_page(url_ajax,response,page_num=1,callback=self.parse_stock)

    def parse_tech(self, response):
        for url in response.css("ul#hidList li a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    # 首页 - 保险 - 行业公司
    def parse_stock(self, response):
        datas = json.loads(re.match(".*?({.*}).*", response.text, re.S).group(1)).get('result')
        for data in datas:
            url=data.get('entityurl')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        
    def parse_hk(self,response):
        for data in response.xpath('//*[@id="inflistBox"]/div'):
            data_url = data.xpath('.//a[@class="newtit"]/@href').get()
            data_time = data.xpath('.//*[@class="clearfix timeShare"]/dt/span/text()').get()
            dt = pubdate_common.handle_pubdate(pubdate_str=data_time, need_detail_time=True)
            pagetime = date2time(time_str=dt)
            yield from over_page(data_url, response, page_time=pagetime, callback=self.parse_detail)
            
            
    def parse_xtyw(self,response):
        for data in response.xpath('//ul[@class="news_list"]/li'):
            data_url = data.xpath('./a/@href').get()
            data_time = data.xpath('./span/text()').get()
            data_time_ = data_time.replace('(', '').replace(')', '').replace('/', '-')
            dt = pubdate_common.handle_pubdate(pubdate_str=data_time_, need_detail_time=True)
            pagetime = date2time(time_str=dt)
            yield from over_page(data_url, response, page_time=pagetime, callback=self.parse_detail)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text','//*[@class="art_contextBox"]/p//text()')  # 正文内容/text_content
        # item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="tip fl"]/a/text()')  # 来源/article_source
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
        return item.load_item()

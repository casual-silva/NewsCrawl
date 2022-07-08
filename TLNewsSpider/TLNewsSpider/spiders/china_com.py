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



class ChinaComSpider(scrapy.Spider):
    name = 'china.com'
    # allowed_domains = ['china.com']
    site_name = '中华网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["宏观舆情", "首页 > 新闻>国际", "https://news.china.com/international/index.html"],
        ["宏观舆情", "首页 > 新闻>国内", "https://news.china.com/domestic/index.html"],
        ["宏观舆情", "首页 >财经>宏观", "https://finance.china.com/domestic/"],
        ["行业舆情", "首页 >财经>证券", "https://finance.china.com/stock/"],
        ["宏观舆情", "首页 >财经>产经", "https://finance.china.com/industrial/"],
        ["行业舆情", "首页 >财经>消费", "https://finance.china.com/consume/"],
        ["行业舆情", "首页 >财经>科技", "https://finance.china.com/tech/"],
        ["行业舆情", "首页 > 财经>酒业要闻", "https://jiu.china.com/jydt/"],
        ["企业舆情", "首页 > 财经>上市公司", "https://finance.china.com/house/ssgs/"],
        ["行业舆情", "首页 > 财经>银行要闻", "https://finance.china.com/bank/yhyw/"],
        ["行业舆情", "首页 > 财经>保险要闻", "https://finance.china.com/insurance/"],
        ["行业舆情", "首页 > 财经>投资要闻", "https://money.china.com/"]
    ]
    
    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification,'num':0}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'news.china.com' in response.url:
            response.meta['time'] = ''
            yield from self.parse_news(response)

        elif 'domestic' in response.url:
            for i in range(1,100):#max 100
                url=f"https://finance.china.com/index/getNewsInfo?page={i}&column_id=11173294"
                response.meta['time']=''
                yield from over_page(url, response, page_num=i, callback=self.parse_domestic)
                # yield scrapy.Request(url,callback=self.parse_domestic,meta=response.meta)
                
        elif '/stock' in response.url:
            for i in range(1,100):#max 100
                url=f"https://finance.china.com/index/getNewsInfo?page={i}&column_id=13003071"
                response.meta['time']=''
                yield from over_page(url, response, page_num=i, callback=self.parse_domestic)
                # yield scrapy.Request(url,callback=self.parse_domestic,meta=response.meta)
                
        elif '/industrial' in response.url:
            for i in range(1,100):#max 100
                url=f"https://finance.china.com/index/getNewsInfo?page={i}&column_id=11173306"
                response.meta['time']=''
                yield from over_page(url, response, page_num=i, callback=self.parse_domestic)
                # yield scrapy.Request(url,callback=self.parse_domestic,meta=response.meta)

        elif '/consume' in response.url:
            for i in range(1,100):#max 100
                url=f"https://finance.china.com/index/getNewsInfo?page={i}&column_id=11173302"
                response.meta['time']=''
                yield from over_page(url, response, page_num=i, callback=self.parse_domestic)
                # yield scrapy.Request(url,callback=self.parse_domestic,meta=response.meta)
        
        elif '/tech' in response.url:
            for i in range(1,100):#max 100
                url=f"https://finance.china.com/index/getNewsInfo?page={i}&column_id=13001906"
                response.meta['time']=''
                yield from over_page(url, response, page_num=i, callback=self.parse_domestic)
                # yield scrapy.Request(url,callback=self.parse_domestic,meta=response.meta)
                
        elif '/jydt' in response.url:
            response.meta['time'] = ''
            response.meta['jiu_url'] = 'https://jiu.china.com/jydt/'
            yield from self.parse_jiu(response)

                
        elif '/ssgs' in response.url:
            response.meta['time'] = ''
            response.meta['jiu_url'] = 'https://finance.china.com/house/news/all/column/ssgs/'
            yield from self.parse_jiu(response)
            
        
        elif 'bank/yhyw' in response.url:
            for i in range(1,100):#max 100
                url=f"https://finance.china.com/bank/news/getNewsInfo?page={i}&column_id=13003105"
                response.meta['time']=''
                yield from over_page(url, response, page_num=i, callback=self.parse_domestic)
                # yield scrapy.Request(url,callback=self.parse_domestic,meta=response.meta)

        elif '/insurance' in response.url:
            for i in range(1, 100):  # max 100
                url = f"https://finance.china.com/index/getNewsInfo?page={i}&column_id=13003065"
                response.meta['time'] = ''
                yield from over_page(url, response, page_num=i, callback=self.parse_domestic)
                # yield scrapy.Request(url, callback=self.parse_domestic, meta=response.meta)

        elif 'money.china' in response.url:
            response.meta['jiu_url'] = 'https://money.china.com/roll/'
            response.meta['time'] = ''
            yield from self.parse_jiu(response)


    def parse_news(self, response):
        for url in response.css("h3.item_title a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
    def parse_domestic(self,response):
        content=json.loads(response.text).get('content')
        for c in content:
            url=c.get('url')
            response.meta['time']=c.get('delivery_time')
            yield scrapy.Request(url,callback=self.parse_detail,meta=response.meta)
            
    def parse_jiu(self,response):
        for url in response.css("h3.tit a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        for i in range(2,100):#max 100
            next_url=f"{response.meta['jiu_url']}p/{i}"
            print(next_url)
            yield from over_page(next_url, response, page_num=i, callback=self.parse_nextjiu)
        # yield scrapy.Request(url,callback=self.parse_jiu,meta=response.meta)
    
    def parse_nextjiu(self, response):
        data=json.loads(response.text).get('data')
        for d in data:
            url = d.get('url')
            response.meta['time'] = d.get('delivery_time')
            yield scrapy.Request(url, callback=self.parse_detail, meta=response.meta)
    
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        if response.meta['time']!='':
            item.add_value('publish_date',response.meta['time'])  # 发布日期/publish_date
        else:
            pd=self.publish_date_rules.extractor(response.text)
            publish_date=pd.replace('年','-').replace('月','-').replace('日','')
            item.add_value('publish_date', publish_date)  # 发布日期/publish_date
        content=response.xpath('//*[@class="article_content"]//p//text()').getall()
        if content==[]:
            content_=response.xpath('//*[@class="arti-detail"]//p/text()').getall()
            content_text=[x.strip() for x in content_ if x.strip() != '']
            item.add_value('content_text',content_text)  # 正文内容/text_content
        else:
            content_text = [x.strip() for x in content if x.strip() != '']
            item.add_value('content_text', content_text)  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//a/span[@class="source"]//text()',re='来源：(.*)')  # 来源/article_source
        item.add_xpath('article_source', '//*[@class="source"]/a/text()')  # 来源/article_source
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

        # 上面获取值可能为空, 追加匹配值
        # item.add_xpath('title', '//h1/text() || //p/h5/text()', re='[标题]{2}:(.*?)')  # 标题/title
        # item.add_css('publish_date', 'p:nth-last-child(-n+5)', re="[0-9]{0,4}年[0-9]{1,2}月[0-9]{1,2}日")  # 发布日期/publish_date
        return item.load_item()

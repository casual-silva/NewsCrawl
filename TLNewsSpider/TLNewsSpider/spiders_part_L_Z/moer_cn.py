# -*- coding: utf-8 -*-

import re
import math
import scrapy
import json
from urllib.parse import urlsplit

from ..utils import date, over_page, date2time,pubdate_common
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class MoerCnSpider(scrapy.Spider):
    name = 'moer.cn'
    allowed_domains = ['moer.cn']
    site_name = '摩尔投研'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 更多 > 个股", "https://www.moer.cn/investment.htm?sortType=time&onColumns=TZGD_HUSHEN"],
        ["行业舆情", "首页 > 更多 > 解盘", "https://www.moer.cn/investment.htm?sortType=time&onColumns=TZGD_HUSHEN"],
        ["企业舆情", "首页 > 更多 > 宏观", "https://www.moer.cn/investment.htm?sortType=time&onColumns=TZGD_HUSHEN"],
        ["企业舆情", "首页 > 更多 > 实盘笔记", "https://www.moer.cn/investment.htm?sortType=time&onColumns=TZGD_HUSHEN"],
        ["企业舆情", "首页 > 更多 > 行业研究", "https://www.moer.cn/investment.htm?sortType=time&onColumns=TZGD_HUSHEN"],
        ["企业舆情", "首页 > 更多 > 新股", "https://www.moer.cn/investment.htm?sortType=time&onColumns=TZGD_HUSHEN"],
        ["企业舆情", "首页 > 更多 > 学堂", "https://www.moer.cn/investment.htm?sortType=time&onColumns=TZGD_HUSHEN"],
        ["企业舆情", "首页 > 更多 > 港股", "https://www.moer.cn/investment.htm?sortType=time&onColumns=TZGD_HUSHEN"],
        ["企业舆情", "首页 > 更多 > 美股", "https://www.moer.cn/investment.htm?sortType=time&onColumns=TZGD_HUSHEN"],
        ["企业舆情", "首页 > 更多 > 理财", "https://www.moer.cn/investment.htm?sortType=time&onColumns=TZGD_HUSHEN"],
    ]

    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            #若不需要用到num来传递次数，则可删去
            meta = {'classification': classification,'num':0,'catlog':catlog}
            yield scrapy.Request(url, callback=self.parse, meta=meta,dont_filter=True)

    def parse(self, response):
        # 详情页
        # post请求的遍历页码的翻页
        url = 'https://www.moer.cn/investment_findPageList.htm?'
        if '个股' in response.meta['catlog']:
            for i in range(1,101):
                data={'price': 'all','authorType': '1','sortType': 'time','firstLevelLabel': 'a','page': str(i)}
                yield from over_page(url,response,callback=self.parse_jijing,formdata=data,page_num=i-3)
                
        elif '解盘' in response.meta['catlog']:
            for i in range(1,51):
                data={'price': 'all','authorType': '1','sortType': 'time','firstLevelLabel': 'b','page': str(i)}
                yield from over_page(url,response,callback=self.parse_jijing,formdata=data,page_num=i)
                
        elif '宏观' in response.meta['catlog']:
            for i in range(1,26):
                data={'price': 'all','authorType': '1','sortType': 'time','firstLevelLabel': 'c','page': str(i)}
                yield from over_page(url,response,callback=self.parse_jijing,formdata=data,page_num=i)
                
        elif '实盘笔记' in response.meta['catlog']:
            for i in range(1,11):
                spbj_data = {'price': 'all','authorType': '1','sortType': 'time','firstLevelLabel': 'd','page': str(i)}
                yield from over_page(url,response,callback=self.parse_jijing,formdata=spbj_data,page_num=i)
                
        elif '行业研究' in response.meta['catlog']:
            for i in range(1,16):
                data={'price': 'all','authorType': '1','sortType': 'time','firstLevelLabel': 'e','page': str(i)}
                yield from over_page(url,response,callback=self.parse_jijing,formdata=data,page_num=i)
                
        elif '新股' in response.meta['catlog']:
            for i in range(1,6):
                data={'price': 'all','authorType': '1','sortType': 'time','firstLevelLabel': 'f','page': str(i)}
                yield from over_page(url,response,callback=self.parse_jijing,formdata=data,page_num=i)
        
        elif '学堂' in response.meta['catlog']:
            for i in range(1,6):
                data={'price': 'all','authorType': '1','sortType': 'time','firstLevelLabel': 'g','page': str(i)}
                yield from over_page(url,response,callback=self.parse_jijing,formdata=data,page_num=i)
                
        elif '港股' in response.meta['catlog']:
            for i in range(1,6):
                data={'price': 'all','authorType': '1','sortType': 'time','firstLevelLabel': 'h','page': str(i)}
                yield from over_page(url,response,callback=self.parse_jijing,formdata=data,page_num=i)
                
        elif '美股' in response.meta['catlog']:
            for i in range(1,11):
                data={'price': 'all','authorType': '1','sortType': 'time','firstLevelLabel': 'i','page': str(i)}
                yield from over_page(url,response,callback=self.parse_jijing,formdata=data,page_num=i)
                
        elif '理财' in response.meta['catlog']:
            for i in range(1,10):
                data={'price': 'all','authorType': '1','sortType': 'time','firstLevelLabel': 'j','page': str(i)}
                yield from over_page(url,response,callback=self.parse_jijing,formdata=data,page_num=i)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        for data in response.xpath('//*[@class="item-main"]'):
            data_url=data.xpath('./h3/a/@href').get()
            url=f"https://www.moer.cn/{data_url}"
            data_time=data.xpath('.//*[@class="item-info"]/em/text()').get()
            hp=pubdate_common.handle_pubdate(data_time)
            pagetime=date2time(date_str=hp.strip())
            yield from over_page(url,response,page_num=1,page_time=pagetime,callback=self.parse_detail)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', pubdate_common.handle_pubdate(self.publish_date_rules.extractor(response.text),need_detail_time=True))  # 发布日期/publish_date
        item.add_xpath('content_text','//*[@class="article-daily article-daily-first"]/p//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_css('article_source', '.source .ly a:first-child::text')  # 来源/article_source
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

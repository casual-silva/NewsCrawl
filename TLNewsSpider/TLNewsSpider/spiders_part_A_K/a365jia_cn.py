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



class A365jiaCnSpider(scrapy.Spider):
    name = '365jia.cn'
    allowed_domains = ['365jia.cn']
    site_name = '万家热线'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页>资讯", "http://365jia.cn/news/"]
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
        yield from self.parse_jijing(response)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        cat_id=response.xpath('//*[@id="cat_id"]/@value').get()
        for i in range(1,21):
            url=f"http://365jia.cn/news/index2019/list?page={i}&id={cat_id}"
            yield from over_page(url,response,page_num=i,callback=self.parse_baoxian)

    # 遍历url翻页方式
    def parse_baoxian(self, response):
        for oc in response.xpath('//*[@class="pt20 pb20 news_list_info"]'):
            data=oc.xpath('./p[@class="fz20 lh28"]/@onclick').get()
            if data == None:
                print('Its None!')
            else:
                list=re.findall('window.open\((.*),',data)
                url_=''.join(list)
                url=url_.replace("'",'')
            pt=oc.xpath('.//span[@class="pr10"]/text()').get()
            pagetime=date2time(date_str=pt)
     
            yield from over_page(url,response,page_num=1,page_time=pagetime,callback=self.parse_detail)
    
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        pd=self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('\n            ',' ')
        item.add_value('publish_date',publish_date )  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="pl30 cor_2 fz16"]/span[3]/text()',re='来源：(.*)')  # 来源/article_source
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

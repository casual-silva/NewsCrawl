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



class JjckbCnSpider(scrapy.Spider):
    name = 'jjckb.cn'
    allowed_domains = ['jjckb.cn','qc.wa.news.cn']
    site_name = '经济参考网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 国资国企 > 央企动态", "http://www.jjckb.cn/gzgqyqdt.htm"],
        ["企业舆情", "首页 > 国资国企 > 上市公司", "http://www.jjckb.cn/gzgqssgs.htm"],
        ["企业舆情", "首页  >  新华企业资讯", "http://www.jjckb.cn/xhqyzx_list.htm"],
        ["企业舆情", "首页 > 公司", "http://www.jjckb.cn/gs.htm"]
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
        if 'cn/gs.htm' in  response.url:
           for i in range(1,21):
               url=f"http://qc.wa.news.cn/nodeart/list?nid=11100292&pgnum={i}&cnt=50&attr=&tp=1&orderby=1"
               yield from over_page(url,response,page_num=i,callback=self.parse_baoxian)
               
        else:
            yield from self.parse_jijing(response)

    def parse_jijing(self, response):
        for data in response.xpath('//*[@class="box_left"]/ul/li'):
            url=data.xpath('./a/@href').get()
            data_time=data.xpath('./span/text()').get()
            pagetime=date2time(min_str=data_time)
            yield from over_page(url,response,page_num=1,page_time=pagetime,callback=self.parse_detail)

    # 遍历url翻页方式
    def parse_baoxian(self, response):
        html=re.findall('"data":(.*),"totalnum"',response.text)
        for data in html:
            list=json.loads(data).get('list')
            for li in list:
                LinkUrl = li.get('LinkUrl')
                PubTime = li.get('PubTime')
                pagetime = date2time(time_str=PubTime)
                yield from over_page(LinkUrl, response, page_num=1, page_time=pagetime, callback=self.parse_detail)
        

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title','//*[@class="top_tit"]/text()')  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="sj_scro"]/span[3]/text()',re='来源：\r\n(.*)')  # 来源/article_source
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

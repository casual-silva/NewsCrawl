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



class CrccCnSpider(scrapy.Spider):
    name = 'crcc.cn'
    allowed_domains = ['crcc.cn']
    site_name = '中国铁建'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["宏观舆情", "首页>企业介绍>品牌服务", "http://hceb.crcc.cn/col/col6534/index.html"],
        ["行业舆情", "首页>新闻中心>行业动态", "http://hceb.crcc.cn/col/col6536/index.html"],
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
        if '/col6534/index.html' in response.url:
            yield from self.parse_jijing(response)

        elif '/col6536/index.html' in response.url:
            url='http://hceb.crcc.cn/module/web/jpage/dataproxy.jsp?startrecord=1&endrecord=45&perpage=15'
            data={
                     'col': '1','appid': '1','webid': '28','path': '/',
                'columnid': '6536','sourceContentType': '1','unitid': '39459',
            'webname': '中国铁建港航局集团有限公司','permissiontype': '0'
            }
            yield scrapy.FormRequest(url,callback=self.parse_baoxian,meta=response.meta,formdata=data)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        href=re.findall('class="piclist" href="(.*?)" ',response.text)
        for url in href:
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    # 遍历url翻页方式
    def parse_baoxian(self, response):
        data_list=re.findall('<a (.*?)</span>',response.text)
        for data in data_list:
            url_list=re.findall('href="(.*?)" ',data)
            date_list=re.findall('<span>(.*)',data)
            date_str=''.join(date_list)
            url_str=''.join(url_list)
            url=f"http://hceb.crcc.cn{url_str}"
            pagetime=date2time(date_str=date_str)
            yield from over_page(url,response,page_num=1,page_time=pagetime,callback=self.parse_detail)
            


    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title','//*[@class="r_t_left"]/text()')  # 标题/title
        item.add_xpath('title','//*[@class="wzy_t2"]/text()')  # 标题/title
        pd=self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('年','-').replace('月','-').replace('日','')
        item.add_value('publish_date',publish_date)  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="wzy_t_bottom"]/span[1]/text()[2]')  # 来源/article_source
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

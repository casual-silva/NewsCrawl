# -*- coding: utf-8 -*-
import json
import re
import math
import scrapy
from urllib.parse import urlsplit

from ..utils import date, over_page
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class LinkshopComSpider(scrapy.Spider):
    name = 'linkshop.com'
    allowed_domains = ['linkshop.com']
    site_name = '联商网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页>资讯", "http://www.linkshop.com/news/"],
        ["行业舆情", "首页>数据>财报", "http://www.linkshop.com/data/cb/"],
        ["行业舆情", "首页>数据>社零", "http://www.linkshop.com/data/cb/"],
        ["行业舆情", "首页>数据>行业", "http://www.linkshop.com/data/cb/"]
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
        if 'linkshop.com/news/' in  response.url:
            for i in range(1,3000):
                url='http://www.linkshop.com/Web/News_Index.aspx'
                data={'isAjax': '1','action':'zixun_zx','pageNo': str(i),'tab': 'zx'}
                yield from over_page(url,response,callback=self.parse_Articles,formdata=data,page_num=i)
                
        elif 'linkshop.com/data/cb/' in  response.url:
            for i in range(1,3000):
                url='http://www.linkshop.com/Web/DataJournalismlist.aspx'
                cb_data={'isAjax': '1','action':'shuju_caibao','pageNo': str(i),'tab': 'cb'}
                sl_data = {'isAjax': '1', 'action': 'shuju_sheling', 'pageNo': str(i), 'tab': 'sl'}
                hy_data = {'isAjax': '1', 'action': 'shuju_hangye', 'pageNo': str(i), 'tab': 'hy'}
                yield from over_page(url,response,callback=self.parse_Articles,formdata=cb_data,page_num=i)
                yield from over_page(url,response,callback=self.parse_Articles,formdata=sl_data,page_num=i)
                yield from over_page(url,response,callback=self.parse_Articles,formdata=hy_data,page_num=i)
                
    # 下一页的翻页方式
    def parse_Articles(self, response):
        data=json.loads(response.text).get('Data')
        for d in data:
            url=d.get('APage')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
            
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text', '//*[@class="page"]//p//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="author"]/text()')  # 来源/article_source
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

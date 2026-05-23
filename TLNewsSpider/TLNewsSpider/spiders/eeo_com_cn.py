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



class EeoComCnSpider(scrapy.Spider):
    name = 'eeo.com.cn'
    allowed_domains = ['eeo.com.cn']
    site_name = '经济观察网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 上市公司", "http://www.eeo.com.cn/ssgsn/"],
        ["行业舆情", "首页 > 汽车", "http://www.eeo.com.cn/qiche/"],
        ["行业舆情", "首页 > TMT", "http://www.eeo.com.cn/tmt/"],
        ["行业舆情", "首页 > 地产", "http://www.eeo.com.cn/dichan/"]
    ]
    
    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id
        
    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification,}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        for url in response.url:
            yield from self.parse_eeo(response)
    
    def parse_eeo(self,response):
        code_list=['']
        a=','
        for xp in response.xpath('//ul[@id="lyp_article"]/li/div/span'):
            url=xp.xpath('./a/@href').get()
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
            code=xp.xpath('./@data-cid').get()
            code_list.append(code)
        code_list.pop(0)
        next_code=a.join(code_list)
        id=response.xpath('//*[@id="catid_lyp"]/@value').get()
            
        # 翻页
        for i in range(1,50):
            t = time.time()
            code_url = f'http://app.eeo.com.cn/?app=wxmember&controller=index&action=getMoreArticle&catid={id}&allcid={next_code}&page={i}&_={int(round(t * 1000))}'
            yield from over_page(code_url, response, page_num=i, callback=self.parse_code)
        # #

    # 首页 - 保险 - 行业公司
    def parse_code(self, response):
        data=json.loads(re.match(".*?({.*}).*", response.text, re.S).group(1)).get('article')
        for d in data:
            url=d.get('url')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_css('article_source', '.source .ly a:first-child::text')  # 来源/article_source
        item.add_value('author','经济观察报')  # 作者/author
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

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



class SemiOrgCnSpider(scrapy.Spider):
    name = 'semi.org.cn'
    allowed_domains = ['semi.org.cn']
    site_name = '汽车电子应用'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页>智能网联", "https://www.semi.org.cn/site/ecar/column/cd3871ebbaef4a5f95cdedc862260cf2.html"],
        ["企业舆情", "首页>辅助驾驶", "https://www.semi.org.cn/site/ecar/column/37c07674056c4e01a06a0c5ff4d26576.html"],
        ["企业舆情", "首页>娱乐导航", "https://www.semi.org.cn/site/ecar/column/1b5332e904b2458eba48c91df8a8188f.html"],
        ["企业舆情", "首页>车载照明", "https://www.semi.org.cn/site/ecar/column/39a927e03dec4dfaa28ce6f014b749e3.html"],
        ["企业舆情", "首页>新能源车", "https://www.semi.org.cn/site/ecar/column/e9b7cdea98c649f59831c8ec0ba9bb7d.html"],
        ["企业舆情", "首页>功率器件", "https://www.semi.org.cn/site/ecar/column/365698170cf34cd89d7a970822f29f89.html"]
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
        for url in response.css(".harticle h2 a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="source"]/span/text()')  # 来源/article_source
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

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



class EastmoneyComSpider(scrapy.Spider):
    name = 'eastmoney.com'
    allowed_domains = ['eastmoney.com']
    site_name = '东方财富网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 债券频道 > 债券资讯", "https://bond.eastmoney.com/a/czqxw.html"],
        ["企业舆情", "首页 > 银行频道 > 银行导读", "https://bank.eastmoney.com/a/cyhdd.html"],
        ["行业舆情", "首页 > 保险频道 > 行业资讯", "https://insurance.eastmoney.com/a/chyzx.html"],
        ["企业舆情", "首页 > 保险频道 > 公司资讯", "https://insurance.eastmoney.com/a/cgsxw.html"],
        ["企业舆情", "首页 > 信托频道 > 信托公司", "https://trust.eastmoney.com/a/cxtgs.html"],
        ["企业舆情", "首页 > 期权频道 > 期权导读", "https://option.eastmoney.com/a/cqqdd.html"],
        ["企业舆情", "首页 > 股票频道 > 美股 > 美股公司", "https://stock.eastmoney.com/a/cmggs.html"],
        ["企业舆情", "首页 > 黄金频道 > 黄金导读", "https://gold.eastmoney.com/a/chjdd.html"],
        ["企业舆情", "首页 > 财经频道 > 焦点 > 证券聚焦", "http://finance.eastmoney.com/a/czqyw.html"],
        ["企业舆情", "首页 > 港股频道 > 公司报道", "http://hk.eastmoney.com/a/cgsbd.html"],
        ["企业舆情", "首页 > 股票频道 > 美股 > 中国概念股", "http://stock.eastmoney.com/a/czggng.html"],
        ["企业舆情", "首页 > 股票频道 > 美股 > 欧美", "http://stock.eastmoney.com/a/cmgpj.html"],
        ["企业舆情", "首页 > 股票频道 > 个股 > 公司评级", "http://stock.eastmoney.com/a/cgspj.html"],
        ["企业舆情", "首页 > 股票频道 > 个股 > 公司研究", "http://stock.eastmoney.com/a/cgsyj.html"],
        ["企业舆情", "首页 > 财经频道 > 焦点 > 公司资讯", "http://finance.eastmoney.com/a/cgsxw.html"],
        ["企业舆情", "首页 > 港股频道 > 港股聚焦", "http://hk.eastmoney.com/a/cggyw.html"],
        ["企业舆情", "首页 > 港股频道 > AH股动态", "http://hk.eastmoney.com/a/cahgdt.html"],
        ["企业舆情", "首页 > 股票频道 > 个股 > 公司研究", "https://stock.eastmoney.com/a/cgsyj.html"],
        ["企业舆情", "首页 > 港股频道 > 个股研究", "http://hk.eastmoney.com/a/cggyj.html"],
        ["企业舆情", "首页 > 港股频道 > 港股导读", "http://hk.eastmoney.com/a/cggdd.html"],
        ["企业舆情", "首页 > 外汇导读", "http://forex.eastmoney.com/a/cwhxw.html"]
    ]

    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            url_=re.findall('(.*)/a/',url)
            next_url=''.join(url_)
            meta = {'classification': classification,'num':0,'url':next_url}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        yield from self.parse_index(response)

    # 首页>基金
    def parse_index(self, response):
        for url in response.css("#newsListContent li div p a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        page=response.xpath('//a[text()="下一页"]/@href').get()
        next_url = f"{response.meta['url']}/a/{page}"
        response.meta['num'] += 1
        yield from over_page(next_url, response, page_num=response.meta['num'], callback=self.parse)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        pb=self.publish_date_rules.extractor(response.text)
        publish_date=pb.replace('年','-').replace('月','-').replace('日','')
        item.add_value('publish_date',publish_date)
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="item"][2]/a/text()')
        item.add_xpath('article_source', '//*[@class="item"][3]//text()',re='来源：([\s\S]*)')
        item.add_xpath('article_source', '//*[@class="item"][2]//text()',re='来源：([\s\S]*)') # 来源/article_source
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

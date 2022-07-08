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



class SznewsComSpider(scrapy.Spider):
    name = 'sznews.com'
    allowed_domains = ['sznews.com']
    site_name = '深圳新闻网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "深圳新闻网首页 > 产经 > 财经 > 银行", "https://www.sznews.com/banking/node_124667.htm"],
        ["企业舆情", "深圳新闻网首页 > 产经 > 财经 > 保险", "https://www.sznews.com/banking/node_124668.htm"],
        ["企业舆情", "深圳新闻网首页 > 产经 > 财经 > 理财", "https://www.sznews.com/banking/node_124679.htm"],
        ["企业舆情", "首页 > 财经 > 股票 > A股 > 公司资讯", "https://www.sznews.com/stock/node_240150.htm"],
        ["企业舆情", "首页 > 财经 > 股票 > 港股 > 公司资讯", "https://www.sznews.com/stock/node_240154.htm"],
        ["企业舆情", "首页 > 房产 > 房产新闻", "https://dc.sznews.com/node_204507.htm"],
        ["企业舆情", "首页 > 房产 > 楼市快递", "https://dc.sznews.com/node_208227.htm"],
        ["宏观舆情", "首页 > 时事 > 国内", "https://news.sznews.com/node_18234.htm"],
        ["宏观舆情", "首页 > 时事 > 国际", "https://news.sznews.com/node_150128.htm"],
        ["行业舆情", "首页 > 消费 >  汽车", "https://auto.sznews.com/node_206009.htm"]
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
        for data in response.xpath('//*[@class="list-pt-li cf"]'):
            data_url=data.xpath('./a[1]/@href').get()
            data_time=data.xpath('.//*[@class="date"]/text()').get()
            pagetime=date2time(date_str=data_time)
            yield from over_page(data_url,response,page_num=1,page_time=pagetime,callback=self.parse_detail)

        # 翻页
        page=response.xpath('//a[text()="下一页"]/@href').get()
        response.meta['num'] += 1
        yield from over_page(page, response, page_time=pagetime, page_num=response.meta['num'], callback=self.parse)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="a_source"]/text()',re='来源： (.*)')  # 来源/article_source
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

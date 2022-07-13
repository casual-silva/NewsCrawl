# -*- coding: utf-8 -*-
import json
import re
import math
import scrapy
from urllib.parse import urlsplit

from ..utils import date, date2time,over_page
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor


class IfengComSpider(scrapy.Spider):
    name = 'ifeng.com'
    allowed_domains = ['ifeng.com']
    site_name = '凤凰网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "财经 > 证券 > 上市公司", "https://finance.ifeng.com/shanklist/1-62-83-/"],
        ["行业舆情", "首页 > 旅游", "https://travel.ifeng.com/shanklist/33-60139-"],
        ["企业舆情", "首页 > 财经>股票 > 新股", "https://finance.ifeng.com/ipo/"],
        ["企业舆情", "首页 > 股票 > 上市公司", "https://finance.ifeng.com/shanklist/1-62-83-"],
        ["企业舆情", "首页 > 港股 > 公司动态", "https://finance.ifeng.com/shanklist/1-69-35250-"],
        ["企业舆情", "安徽 > 产经 > 正文", "https://ah.ifeng.com/shanklist/200-214-216346-/"]
    ]

    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        result = response.selector.re('var allData = (.*?});')
        if result:
            result = json.loads(result[0])
            newsstream = result['newsstream']
            columnId = result['columnId']
            response.meta['columnId'] = columnId
            for item in newsstream:
                url = item['url']
                yield response.follow(url, callback=self.parse_detail, meta=response.meta)
                # break
            # 请求下一页
            yield from self.get_next_page(response, item)

    def get_next_page(self, response, item):
        id = item['id']
        newsTime = int(date2time(time_str=item['newsTime']))
        columnId = response.meta['columnId']
        next_page_url = f'https://shankapi.ifeng.com/shanklist/_/getColumnInfo/_/default/{id}/{newsTime}/20/{columnId}/getColumnInfoCallback?callback=getColumnInfoCallback&_=16401408536691'
        if 'finance.ifeng.com/ipo' in response.url or 'dynamicFragment' in response.url:
            next_page_url = f'https://shankapi.ifeng.com/shanklist/_/getColumnInfo/_/dynamicFragment/{id}/{newsTime}/20/240131/getColumnInfoCallback?callback=getColumnInfoCallback&_=16401456329751'
        yield response.follow(next_page_url, callback=self.parse_page, meta=response.meta)

    def parse_page(self, response):
        _json_data = response.selector.re('getColumnInfoCallback\((.*?})\)')
        json_data = json.loads(_json_data[0])
        isEnd = json_data['data']['isEnd']
        # print('>>>>>>>>>>>>', isEnd)
        for item in json_data['data']['newsstream']:
            url = item['url']
            newsTime=item['newsTime']
            page_time=date2time(time_str=newsTime)
            yield from over_page(url,response,page_num=1,page_time=page_time,callback=self.parse_detail)
            # break
        if not isEnd:
            yield from self.get_next_page(response, item)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text','//*[@class="text-3w2e3DBc"]/p//text()')  # 正文内容/text_content
        # 自定义规则
        item.add_css('article_source', '.source-qK4Su0-- a::text')  # 来源/article_source
        item.add_css('author', 'script::text', re='"editorName":"(.{2,8})","editorCode"')  # 作者/author

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
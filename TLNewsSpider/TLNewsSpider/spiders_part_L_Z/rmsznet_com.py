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
from lxml import etree


class RmsznetComSpider(scrapy.Spider):
    name = 'rmsznet.com'
    allowed_domains = ['rmsznet.com']
    site_name = '人民报社-人民数字'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["宏观舆情", "首页 >  财经", "http://www.rmsznet.com/57.html"],
        ["行业舆情", "首页 >  汽车", "http://www.rmsznet.com/103.html"],
        ["宏观舆情", "首页 >  新闻", "http://www.rmsznet.com/56.html"],
        ["宏观舆情", "首页 >  上海 > 财经", "http://sh.rmsznet.com/616.html"],
        ["地区舆情", "首页 >  江苏 > 金融频道", "http://js.rmsznet.com/720.html"],
        ["地区舆情", "首页 >  安徽 > 财经", "http://ah.rmsznet.com/619.html"],
        ["地区舆情", "首页 >  河南 > 财经", "http://henan.rmsznet.com/199.html"],
        ["行业舆情", "首页 >  河南 > 房产", "http://henan.rmsznet.com/205.html"],
        ["地区舆情", "首页 >  四川 > 财经", "http://sc.rmsznet.com/262.html"],
        ["地区舆情", "首页 >  山东 > 财经", "http://sd.rmsznet.com/183.html"],
        ["地区舆情", "首页 >  西北 > 财经", "http://sx.rmsznet.com/215.html"],
        ["地区舆情", "首页 >  福建 > 财经", "http://fj.rmsznet.com/459.html"],
        ["地区舆情", "首页 >  广东 > 财经", "http://gd.rmsznet.com/333.html"],
        ["地区舆情", "首页 >  吉林 > 财经", "http://jl.rmsznet.com/495.html"],
        ["地区舆情", "首页 >  黑龙江 > 财经", "http://hlj.rmsznet.com/486.html"],
        ["地区舆情", "首页 >  河北 > 财经", "http://hebei.rmsznet.com/769.html"]
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
        code=re.findall('(.*)/',response.url)
        url_code=''.join(code)
        for data in response.xpath('//*[@class="thumbnail news-catalogue"]'):
            data_url=data.xpath('.//*[@id="newsListTitle"]/@data-id').get()
            data_time=data.xpath('.//*[@class="times"]/text()').get()
            url=f"http://app.rmsznet.com/api/rmrb/v1/GetArticleDetail?articleid={data_url}"
            dt=data_time.replace('/','-')
            response.meta['pd']=dt
            pagetime=date2time(time_str=dt)
            yield from over_page(url,response,page_num=1,page_time=pagetime,callback=self.parse_detail)
        #
        # # 翻页
        page=response.xpath('//a[text()="下一页"]/@href').get()
        next_url=f"{url_code}/{page}"
        response.meta['num'] += 1
        yield from over_page(next_url, response, page_time=pagetime, page_num=response.meta['num'], callback=self.parse)

    def parse_detail(self, response):
        Data=json.loads(response.text).get('Data')
        for data in Data:
            title=data.get('title')
            content=data.get('content')
            Aauthor=data.get('Aauthor')
            source=data.get('source')
            html=etree.HTML(content)
            text=html.xpath('//text()')
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        item.add_value('title', title)  # 标题/title
        item.add_value('publish_date',response.meta['pd'])  # 发布日期/publish_date
        item.add_value('content_text', text)  # 正文内容/text_content
        # 自定义规则
        item.add_value('article_source', source)  # 来源/article_source
        item.add_value('author',Aauthor)  # 作者/author
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

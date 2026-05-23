# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time

from ..utils import date,over_page,date2time,pubdate_common
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class HuxiuComSpider(scrapy.Spider):
    name = 'huxiu.com'
    allowed_domains = ['huxiu.com']
    site_name = '虎嗅网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页>资讯>频道>车与出行", "https://www.huxiu.com/channel/21.html"],
        ["行业舆情", "首页>资讯>频道>医疗健康", "https://www.huxiu.com/channel/111.html"],
        ["行业舆情", "首页>资讯>频道>金融地产", "https://www.huxiu.com/channel/102.html"],
        ["行业舆情", "首页>资讯>频道>财经", "https://www.huxiu.com/channel/115.html"]
    ]

    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification,'url':url}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        id_=re.findall('channel/(.*).html',response.meta['url'])
        id=''.join(id_)
        response.meta['id'] = id
        last_time_=re.findall('"last_time":"(.*?)"',response.text)
        last_time=''.join(last_time_)
        for data in response.xpath('//div[@class="tibt-card__bottom"]'):
            data_url=data.xpath('./a[1]/@href').get()
            data_time=data.xpath('.//*[@class="status__date"]/text()').get()
            url=f"https://www.huxiu.com{data_url}"
            data_time_=pubdate_common.handle_pubdate(pubdate_str=data_time,need_detail_time=True)#pubdate_str为需要转换的时间字符串
            pagetime=date2time(time_str=data_time_)
            yield from over_page(url,response,page_time=pagetime,callback=self.parse_detail)
        
        url_='https://article-api.huxiu.com/web/channel/articleList'
        #异步加载的post请求所带的参数
        body={'platform':'www','last_time':last_time,'channel_id':id}
        yield scrapy.FormRequest(url_,callback=self.parse_articleList,meta=response.meta,formdata=body)

    def parse_articleList(self, response):
        id=response.meta['id']
        data=json.loads(response.text).get('data')
        datalist = data.get('datalist')
        for d in datalist:
            aid=d.get('aid')
            url=f"https://m.huxiu.com/article/{aid}.html"
            
        last_time=''.join(data.get('last_time'))
        if last_time != None:
            body={'platform':'www','last_time':last_time,'channel_id':id}
            yield scrapy.FormRequest(response.url,callback=self.parse_articleList,meta=response.meta,formdata=body)
        #

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title','//h1[@class="article__title"]/text()')
        item.add_xpath('title', '//div[@id="article"]/div[@class="title"]/text()')  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_css('article_source', '.source .ly a:first-child::text')  # 来源/article_source
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

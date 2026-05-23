# -*- coding: utf-8 -*-
import json
import re
import math
import scrapy
from urllib.parse import urlsplit

from ..utils import date, over_page, date2time
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class XuangubaoCnSpider(scrapy.Spider):
    name = 'xuangubao.cn'
    allowed_domains = ['xuangubao.cn']
    site_name = '选股宝'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 7x24快讯", "https://xuangubao.cn/live"]
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
        # for url in response.css(".title_3EhHc a"):
        #     yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        cursor=response.xpath('//@cursor').get()
        subjectids=response.xpath('//@subjectids').get()
        response.meta['subjectids']=subjectids
        next_url=f"https://baoer-api.xuangubao.cn/api/v6/message/newsflash?limit=20&cursor={cursor}&subj_ids={subjectids}&platform=pcweb"
        yield scrapy.Request(url=next_url,callback=self.parse_xhr,meta=response.meta)
        
        
    def parse_xhr(self, response):
        data=json.loads(response.text).get('data')
        messages=data.get('messages')
        next_cursor=data.get('next_cursor')
        for me in messages:
            id=me.get('id')
            created_at=me.get('created_at')
            url=f"https://xuangubao.cn/article/{id}"
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        time_limit=created_at
        next_url = f"https://baoer-api.xuangubao.cn/api/v6/message/newsflash?limit=20&cursor={next_cursor}&subj_ids={response.meta['subjectids']}&platform=pcweb"
        yield from over_page(next_url, response, page_time=int(time_limit),page_num=1, callback=self.parse_xhr)
 
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        title=response.xpath('//*[@class="title_2NdHM"]//text()').get()
        item.add_value('title', title)  # 标题/title
        pd=self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('/','-')
        item.add_value('publish_date',publish_date )  # 发布日期/publish_date
        content=response.xpath('//*[@class="pre_3k5h5"]//text()').getall()
        if content==[]:
            item.add_value('content_text',title)  # 正文内容/text_content
        else:
            item.add_value('content_text', content)  # 正文内容/text_content
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

        # 上面获取值可能为空, 追加匹配值
        # item.add_xpath('title', '//h1/text() || //p/h5/text()', re='[标题]{2}:(.*?)')  # 标题/title
        # item.add_css('publish_date', 'p:nth-last-child(-n+5)', re="[0-9]{0,4}年[0-9]{1,2}月[0-9]{1,2}日")  # 发布日期/publish_date
        return item.load_item()

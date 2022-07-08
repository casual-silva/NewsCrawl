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
from lxml import etree



class JiemianComSpider(scrapy.Spider):
    name = 'jiemian.com'
    allowed_domains = ['jiemian.com']
    site_name = '界面新闻'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 商业 > 快讯", "https://www.jiemian.com/lists/2.html"],
        ["企业舆情", "首页>快报>公司头条", "https://www.jiemian.com/lists/1322kb.html"],
        ["行业舆情", "首页>股市>股市", "https://www.jiemian.com/lists/464.html"],
        ["宏观舆情", "首页>股市>宏观", "https://www.jiemian.com/lists/174.html"]
    ]

    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            #若不需要用到num来传递次数，则可删去
            meta = {'classification': classification,'num':0,'count':3}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        #直接在parse里遍历页码的翻页
        if 'lists/2.html' in  response.url:
           for i in range(1,30):
               response.meta['num'] +=1
               url=f"https://a.jiemian.com/index.php?m=newLists&a=loadMore&tid=105&page={i}&tpl=sub-card-list&list_type="
               yield from over_page(url,response,page_num=i,callback=self.parse_page)
               
        elif 'lists/1322kb.html' in response.url:
            yield from self.parse_baoxian(response)
            
        elif 'lists/464.html' in  response.url:
           for i in range(1,30):
               response.meta['num'] +=1
               url=f"https://a.jiemian.com/index.php?m=newLists&a=loadMore&tid=464&page={i}&tpl=sub-card&repeat=&list_type=category"
               yield from over_page(url,response,page_num=i,callback=self.parse_page)
               
        elif 'lists/174.html' in  response.url:
           for i in range(1,30):
               response.meta['num'] +=1
               url=f"https://a.jiemian.com/index.php?m=newLists&a=loadMore&tid=514&page={i}&tpl=sub-card&list_type="
               yield from over_page(url,response,page_num=i,callback=self.parse_page)


    def parse_page(self,response):
        html_list=re.findall('jsonpReturn[(](.*)\);',response.text)
        for list in html_list:
            html=json.loads(list).get('html')
            page_html = etree.HTML(html)
            url_list=page_html.xpath('//li/div/a/@href')
            for url in url_list:
                yield response.follow(url, callback=self.parse_detail, meta=response.meta)
            

    # 下一页的翻页方式
    def parse_jijing(self, response):
        for url in response.css(".newslist_content li a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        page=response.xpath('//a[text()="下一页"]/@href').get()
        next_url=f"https://www.21ic.com{page}"
        response.meta['num'] += 1
        yield from over_page(next_url, response, page_num=response.meta['num'], callback=self.parse)

    # 遍历url翻页方式
    def parse_baoxian(self, response):
        # for url in response.css("a.logStore"):
        #     yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        for list in response.xpath('//*[@class="columns-right-center__newsflash-items"]/li'):
            url=list.xpath('.//*[@class="logStore"]/@href').get()
            dt=list.xpath('./div/@data-time').get()
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        next_url = f"https://papi.jiemian.com/page/api/kuaixun/getlistmore?cid=1322kb&start_time={dt}&page=2&tagid=1322"
        yield response.follow(next_url, callback=self.parse_result, meta=response.meta)
        
    def parse_result(self,response):
        result=json.loads(response.text).get('result')
        list=result.get('list')
        for li in list:
            id=li.get('id')
            publishtime=li.get('publishtime')
            url=f"https://www.jiemian.com/article/{id}.html"
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        next_url = f"https://papi.jiemian.com/page/api/kuaixun/getlistmore?cid=1322kb&start_time={publishtime}&page={response.meta['count']}&tagid=1322"
        response.meta['num'] += 1
        response.meta['count'] += 1
        yield from over_page(next_url, response, page_num=response.meta['num'], callback=self.parse_result)


    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        pd=self.publish_date_rules.extractor(response.text)
        publish_date=pd.replace('/','-')
        item.add_value('publish_date',publish_date )  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="article-info"]/p//text()',re='来源：(.*)')  # 来源/article_source
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

# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time

from ..utils import date
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class JrjComCnSpider(scrapy.Spider):
    name = 'jrj.com.cn'
    allowed_domains = ['jrj.com.cn']
    site_name = '金融界美股'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "金融界首页 > 美股 > 中国概念股", "http://usstock.jrj.com.cn/"],
        ["企业舆情", "金融界首页 > 科技 > IT业界", "http://finance.jrj.com.cn/tech/xwk/201801/20180101_1.shtml"],
        ["企业舆情", "首页 > 股票 > 上市公司", "http://stock.jrj.com.cn/xwk/201801/20180101_1.shtml"],
        ["企业舆情", "金融界首页 > 财经频道 >  公司新闻", "http://finance.jrj.com.cn/xwk/201801/20180101_1.shtml"],
        ["企业舆情", "金融界首页 > 港股频道 > 公司新闻", "http://hk.jrj.com.cn/xwk/201801/20180101_1.shtml"],
        ["企业舆情", "金融界首页 > 理财频道 > 理财资讯", "http://money.jrj.com.cn/list/lczx.shtml"],
        ["企业舆情", "金融界首页 > 观点", "http://opinion.jrj.com.cn/"],
        ["企业舆情", "金融界首页>财经频道> 商业资讯", "http://biz.jrj.com.cn/xwk/201801/20180101_1.shtml"],
        ["行业舆情", "首页>期货>焦点新闻", "http://futures.jrj.com.cn/xwk/201801/20180101_1.shtml"]
    ]

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'usstock.jrj' in response.url:
            t=time.time()
            url=f"https://stock.jrj.com.cn/web/getUsstcokNews.jspa?channum=102&infocls=001017&startnum=0&endnum=100&_={int(round(t * 1000))}"
            yield scrapy.Request(url, callback=self.parse_usstock, meta=response.meta)

        elif 'xwk' in response.url:
            yield from self.parse_xwk(response)
            
        elif 'money.jrj.com' in response.url:
            url='https://news.jrj.com.cn/json/news/getNews?erwegg&size=2000&d=f&chanNum=111&infoCls=001003&vname=contents&field=iiid,title,pcinfourl,makedate,comment,detail'
            yield scrapy.Request(url, callback=self.parse_money, meta=response.meta)
            
        elif 'opinion.jrj' in response.url:
            yield from self.parse_opinion(response)
            
    def parse_opinion(self,response):
        for url in response.css('.eliteUl li strong a'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
    # 首页>基金
    def parse_xwk(self, response):
        for url in response.xpath('//ul[@class="list"]/li/a'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        next_url=response.xpath('//a[text()="下一页"]/@href').get()
        if next_url== None:
            pages=response.xpath('//*[text()="后一天"]/@href').get()
            yield response.follow(pages, meta=response.meta)
        else:
            yield response.follow(next_url, meta=response.meta)

    # 首页 - 保险 - 行业公司
    def parse_usstock(self, response):
        data=json.loads(re.match(".*?({.*}).*", response.text, re.S).group(1)).get('result')
        for d in data:
            url=d.get('infoUrl')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        
    def parse_money(self,response):
        data=json.loads(re.match(".*?({.*}).*", response.text, re.S).group(1)).get('data')
        for d in data:
            url=d.get('pcinfourl')
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        title=response.xpath('//meta[@property="og:title"]/@content').get()
        item.add_value('title', title)  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        sou=response.xpath('//div[@class="titInf210118"]/p/i[1]/text()').getall()
        source=''.join(sou).replace('【来源：','').replace('】','')
        item.add_value('article_source', source)  # 来源/article_source
        item.add_xpath('article_source','//*[@class="inftop"]/span[2]/text()[2]')
        item.add_xpath('article_source', '//span[@class="urladd"]/text()[2]')
        item.add_xpath('author', '//span[@class="zaname"]/text()[2]')  # 作者/author
        # 默认保存一般无需更改
        item.add_value('spider_time', date())  # 抓取时间
        item.add_value('created_time', date())  # 更新时间
        item.add_value('source_url', response.url)  # 详情网址/detail_url
        item.add_value('site_name', self.site_name)  # 站点名称
        item.add_value('site_url', urlsplit(response.url).netloc)  # 站点host
        item.add_value('classification', response.meta['classification'])  # 所属分类
        # 网页源码  调试阶段注释方便查看日志
        # item.add_value('html_text', response.text)  # 网页源码

        # 上面获取值可能为空, 追加匹配值
        # item.add_xpath('title', '//h1/text() || //p/h5/text()', re='[标题]{2}:(.*?)')  # 标题/title
        # item.add_css('publish_date', 'p:nth-last-child(-n+5)', re="[0-9]{0,4}年[0-9]{1,2}月[0-9]{1,2}日")  # 发布日期/publish_date
        return item.load_item()

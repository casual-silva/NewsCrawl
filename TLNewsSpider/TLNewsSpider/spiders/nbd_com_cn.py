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



class NbdComCnSpider(scrapy.Spider):
    name = 'nbd.com.cn'
    allowed_domains = ['nbd.com.cn']
    site_name = '每经网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["宏观舆情", "首页＞宏观", "http://economy.nbd.com.cn/"],
        ["企业舆情", "首页＞公司", "http://industry.nbd.com.cn/"],
        ["企业舆情", "首页＞汽车＞聚焦", "http://auto.nbd.com.cn/columns/261"],
        ["企业舆情", "首页＞汽车＞新能源", "http://auto.nbd.com.cn/columns/140"],
        ["企业舆情", "首页＞汽车＞科技", "http://auto.nbd.com.cn/columns/1444"],
        ["企业舆情", "首页＞汽车＞电商", "http://auto.nbd.com.cn/columns/132"],
        ["企业舆情", "首页＞汽车＞商用车", "http://auto.nbd.com.cn/columns/131"],
        ["企业舆情", "首页＞汽车＞新出行", "http://auto.nbd.com.cn/columns/1474"],
        ["企业舆情", "首页＞镁刻地产", "http://www.nbd.com.cn/fangchan"],
        ["企业舆情", "每经网 > 公司 >  热点公司", "http://industry.nbd.com.cn/columns/346"]
    ]

    headers = {
        'X-CSRF-Token': 'iK3ixyFifC7vV2N+WLJi4xjDHCQRB7/7YpaH+g3Kwfg=',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'Accept':'*/*;q=0.5, text/javascript, application/javascript, application/ecmascript, application/x-ecmascript',
        'Connection':'keep-alive'
    }

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'economy.nbd' in response.url:
            response.meta['id']='310'
            response.meta['s_name']='economy'
            yield response.follow(response.url, callback=self.parse_economy, meta=response.meta,dont_filter=True)
        
        elif 'http://industry.nbd.com.cn/' == response.url:
            response.meta['id']='338'
            response.meta['s_name']='industry'
            yield response.follow(response.url, callback=self.parse_economy, meta=response.meta,dont_filter=True)

        elif 'auto.nbd.com.cn' in response.url:
            yield from self.parse_auto(response)
            
        elif 'nbd.com.cn/fangchan' in response.url:
            yield from self.parse_fangchan(response)
            
        elif 'nbd.com.cn/columns/346' in response.url:
            yield from self.parse_346(response)
        
    # 首页>基金
    def parse_economy(self, response):
        urls=response.xpath('//*[@class="f-title"]/@href').getall()
        for url in urls:
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        url_code=re.findall('[1-9]\d{6}',url)
        code=''.join(url_code)
        next_url=f"http://{response.meta['s_name']}.nbd.com.cn/columns/{response.meta['id']}?last_article={code}&version_column=v5"
        yield response.follow(next_url, callback=self.parse_next, meta=response.meta,headers=self.headers)
    # 首页 - 保险 - 行业公司
    def parse_next(self, response):
        html=re.findall('www.[^\s]*.html',response.text)
        html_=list(set(html))
        for h in html_:
            h=str(h)
            url=f"http://{h}"
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        url_code = re.findall('[1-9]\d{6}', url)
        code = ''.join(url_code)
        next_url = f"http://{response.meta['s_name']}.nbd.com.cn/columns/{response.meta['id']}?last_article={code}&version_column=v5"
        yield response.follow(next_url, callback=self.parse_next, meta=response.meta, headers=self.headers)
    
    def parse_auto(self,response):
        for url in response.xpath('//*[@class="news-text"]/a'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        for page in response.css('#load_articles'):
            yield response.follow(page, meta=response.meta, callback=self.parse_auto_next, headers=self.headers)

    def parse_auto_next(self, response):
        html = re.findall('//www.nbd.com.cn/articles/[^\s]*.html', response.text)
        html_ = list(set(html))
        for h in html_:
            h = str(h)
            auto_url = f"http:{h}"
            yield response.follow(auto_url, callback=self.parse_detail, meta=response.meta)
        pattern = re.findall('//auto.nbd[^\s]*last_article_pos=[\d]*', response.text)
        pattern_ = ''.join(pattern)
        pattern_url=f"http:{pattern_}"
        yield response.follow(pattern_url, meta=response.meta, callback=self.parse_auto_next,headers=self.headers)
        
    def parse_fangchan(self,response):
        urls = response.xpath('//*[@class="f-title"]/@href').getall()
        for url in urls:
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        url_code = re.findall('[1-9]\d{6}', url)
        code = ''.join(url_code)
        next_url = f"http://www.nbd.com.cn/columns/298?last_article={code}&version_column=v5"
        yield response.follow(next_url, callback=self.parse_fangchan_next, meta=response.meta, headers=self.headers)
        
    def parse_fangchan_next(self, response):
        html=re.findall('www.[^\s]*.html',response.text)
        html_=list(set(html))
        for h in html_:
            h=str(h)
            url=f"http://{h}"
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        url_code = re.findall('[1-9]\d{6}', url)
        code = ''.join(url_code)
        next_url = f"http://www.nbd.com.cn/columns/298?last_article={code}&version_column=v5"
        yield response.follow(next_url, callback=self.parse_fangchan_next, meta=response.meta, headers=self.headers)
        
    def parse_346(self, response):
        for url in response.css(".u-news-title a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        for page in response.css('.next a'):
            yield response.follow(page, meta=response.meta)
    

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text', '//*[@class="g-articl-text"]/p//text()')  # 正文内容/text_content
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
        # item.add_value('html_text', response.text)  # 网页源码

        # 上面获取值可能为空, 追加匹配值
        # item.add_xpath('title', '//h1/text() || //p/h5/text()', re='[标题]{2}:(.*?)')  # 标题/title
        # item.add_css('publish_date', 'p:nth-last-child(-n+5)', re="[0-9]{0,4}年[0-9]{1,2}月[0-9]{1,2}日")  # 发布日期/publish_date
        return item.load_item()

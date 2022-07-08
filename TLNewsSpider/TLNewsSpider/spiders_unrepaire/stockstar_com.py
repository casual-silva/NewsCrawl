# -*- coding: utf-8 -*-

import scrapy
from urllib.parse import urlsplit
from ..utils import date
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor


class StockstarComSpider(scrapy.Spider):
    name = 'stockstar.com'
    allowed_domains = ['stockstar.com']
    site_name = '证券之星'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        #  首页 > 基金  https://fund.stockstar.com/  页面可分为三个子分类
        ["企业舆情", "首页>基金分析", "https://fund.stockstar.com/list/1297.shtml"],
        ["企业舆情", "首页>基金动态", "https://fund.stockstar.com/list/1565.shtml"],
        ["企业舆情", "首页>基金>基金要闻", "https://fund.stockstar.com/list/1293.shtml"],

        ["企业舆情", "首页>港股", "https://hk.stockstar.com/"],
        ["企业舆情", "首页>外汇>热点追踪", "http://forex.stockstar.com/list/1699.shtml"],
        ["企业舆情", "首页-保险-行业公司", "https://insurance.stockstar.com/list/5031.shtml"],
        ["企业舆情", "首页-银行-银行新闻", "https://bank.stockstar.com/list/1751.shtml"],

        ["企业舆情", "首页>股票>公司新闻", "https://stock.stockstar.com/list/10_1.shtml"],
        ["企业舆情", "首页>股票>中概股", "https://stock.stockstar.com/cnstock/"],
        ["企业研报", "首页>股票>研报>公司研究", "https://stock.stockstar.com/list/3491.shtml"],
        ["行业研报", "首页>股票>研报>行业研究", "https://stock.stockstar.com/list/3489.shtml"],
        ["企业舆情", "首页>股票>创业板>创业板要闻", "https://stock.stockstar.com/list/4049.shtml"],
        ["企业舆情", "首页>股票>科创板>科创板要闻", "https://stock.stockstar.com/list/5379.shtml"],
        ["企业舆情", "首页>股票>三板>新三板公司", "https://stock.stockstar.com/list/5257.shtml"],

        ["行业舆情", "首页>财经>行业新闻", "https://finance.stockstar.com/list/2921.shtml"],
        ["企业舆情", "首页>财经>公司新闻", "https://finance.stockstar.com/list/2863.shtml"]
    ]

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        if 'fund.stockstar.com/list' in response.url:
            yield from self.parse_jijing(response)

        elif 'insurance.stockstar.com/list' in response.url:
            yield from self.parse_baoxian(response)

        elif 'hk.stockstar.com' in response.url:
            yield from self.parse_gangu(response)

        elif 'forex.stockstar.com/list' in response.url:
            yield from self.parse_redian(response)

        elif 'bank.stockstar.com/list' in response.url:
            # 页面和保险一样
            yield from self.parse_baoxian(response)

        # if 'stock.stockstar.com/list/10_1' in response.url:
        elif 'stock.stockstar.com' in response.url:
            # 页面和港股一样
            yield from self.parse_gangu(response)

        elif 'finance.stockstar.com/list' in response.url:
            # 页面和保险一样
            yield from self.parse_baoxian(response)


    # 首页>基金
    def parse_jijing(self, response):
        for url in response.css(".newslist_content li a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        # 翻页
        for page in response.css('#Page a::attr(href)'):
            yield response.follow(page, meta=response.meta)

    # 首页 - 保险 - 行业公司
    def parse_baoxian(self, response):
        for url in response.css('.content li a'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        # 翻页
        for page in response.css('#Page a::attr(href)'):
            yield response.follow(page, meta=response.meta)

    # 首页>港股
    def parse_gangu(self, response):
        for url in response.css('.listnews li a'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        # 翻页
        for page in response.css('#Page a::attr(href),.pageControl a::attr(href)'):
            yield response.follow(page, meta=response.meta)

    # 首页>外汇>热点追踪
    def parse_redian(self, response):
        for url in response.css('.newslist li a'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        # 翻页
        for page in response.css('#Page a::attr(href)'):
            yield response.follow(page, meta=response.meta)

    # 首页>股票>公司新闻
    def parse_gongsixingwen(self, response):
        for url in response.css('.zitop a'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
        # 翻页
        for page in response.css('#Page a::attr(href)'):
            yield response.follow(page, meta=response.meta)

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_css('article_source', '.source .ly a:first-child::text')  # 来源/article_source
        item.add_css('author', '.source #author_baidu a::text')  # 作者/author
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

# -*- coding: utf-8 -*-

import re
import math
import scrapy
import json
from urllib.parse import urlsplit

from ..utils import date, over_page, date2time,pubdate_common
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor
from lxml import etree


class ChinaComCnSpider(scrapy.Spider):
    name = 'china.com.cn'
    allowed_domains = ['china.com.cn','gxfin.com']
    site_name = '中国网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["宏观舆情", "首页 > 新闻", "http://news.china.com.cn/"],
        ["宏观舆情", "首页 > 财经 > 宏观", "http://finance.china.com.cn/news/index.shtml"],
        ["企业舆情", "首页 > 财经 > 证券 > 上市公司", "http://finance.china.com.cn/stock/ssgs/index.shtml"],
        ["行业舆情", "首页 > 财经 > 证券 > 证券要闻", "http://finance.china.com.cn/stock/zqyw/index.shtml"],
        ["行业舆情", "首页 > 财经 > 金融 > 基金", "http://finance.china.com.cn/money/fund/"],
        ["行业舆情", "首页 > 财经 > 金融 > 银行", "http://finance.china.com.cn/money/bank/index.shtml"],
        ["行业舆情", "首页 > 财经 > 金融 > 保险", "http://finance.china.com.cn/money/insurance/index.shtml"],
        ["行业舆情", "首页 > 财经 > 金融 > 金融科技", "http://finance.china.com.cn/money/fintech/index.shtml"],
        ["行业舆情", "首页 > 财经 > 金融 > 新三板", "http://finance.china.com.cn/stock/xsb/index.shtml"],
        ["行业舆情", "首页 > 财经 > 科创板 > 新股", "http://ipo.china.com.cn/"],
        ["行业舆情", "首页 > 财经 > 科创板 > 港股", "http://finance.china.com.cn/stock/hkstock/index.shtml"],
        ["行业舆情", "首页 > 财经 > 科创板 > 美股", "http://finance.china.com.cn/stock/usstock/index.shtml"],
        ["行业舆情", "首页 > 财经 > 科创板 > 创投", "http://finance.china.com.cn/vc/index.shtml"],
        ["宏观舆情", "首页 > 财经 > ESG", "http://finance.china.com.cn/esg/index.shtml"],
        ["行业舆情", "首页 > 财经 > 消费", "http://finance.china.com.cn/consume/index.shtml"],
        ["行业舆情", "首页 > 财经 > 医药", "http://finance.china.com.cn/industry/medicine/"],
        ["行业舆情", "首页 > 财经 > 能源", "http://finance.china.com.cn/industry/energy/"],
        ["行业舆情", "首页 > 财经 > 地产", "http://finance.china.com.cn/house/index.shtml"],
        ["行业舆情", "首页 > 财经 > 汽车", "http://auto.china.com.cn/"],
        ["行业舆情", "首页 > 财经 > 科技", "http://tech.china.com.cn/"]
    ]



    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            #若不需要用到num来传递次数，则可删去
            meta = {'classification': classification,'num':1}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if '/stock/' in response.url:
            yield from self.parse_jijing(response)
            
        elif '/news/' in response.url:
            yield from self.parse_jijing(response)

        elif 'news.china.com.cn' in response.url:
            yield from self.parse_baoxian(response)

        elif '/money/' in response.url:
            code=re.findall('/money/(.*)/',response.url)
            code_=''.join(code)
            url=f"http://app.finance.china.com.cn/news/more_news.php?cnl={code_}&index=0"
            response.meta['next_url']=url
            yield from self.parse_money(response)
            
        elif 'http://ipo.china.com.cn/' == response.url:
            yield from self.parse_ipo(response)
            
        elif '/industry/' in response.url:
            code = re.findall('/industry/(.*)/', response.url)
            code_ = ''.join(code)
            url = f"http://app.finance.china.com.cn/news/more_news.php?cnl={code_}&index=0"
            response.meta['next_url'] = url
            yield from self.parse_money(response)
        
        elif '/esg/' in response.url:
            code = re.findall('com.cn/(.*)/index.shtml', response.url)
            code_ = ''.join(code)
            url = f"http://app.finance.china.com.cn/news/more_news.php?cnl={code_}&index=0"
            response.meta['next_url'] = url
            yield from self.parse_money(response)
        
        elif '/consume/' in response.url:
            code = re.findall('com.cn/(.*)/index.shtml', response.url)
            code_ = ''.join(code)
            url = f"http://app.finance.china.com.cn/news/more_news.php?cnl={code_}&index=0"
            response.meta['next_url'] = url
            yield from self.parse_money(response)
            
        elif '/house/' in response.url:
            code = re.findall('com.cn/(.*)/index.shtml', response.url)
            code_ = ''.join(code)
            url = f"http://app.finance.china.com.cn/news/more_news.php?cnl={code_}&index=0"
            response.meta['next_url'] = url
            yield from self.parse_money(response)
        #
        elif 'http://auto.china.com.cn/' ==response.url:
            url = 'https://app-auto.gxfin.com/news/more_news.php?cnl=auto&index=0'
            response.meta['next_url'] = url
            yield from self.parse_money(response)
            
        elif 'http://tech.china.com.cn/' ==response.url:
            url = 'https://app-tech.gxfin.com/news/more_news.php?cnl=tech&index=0'
            response.meta['next_url'] = url
            yield from self.parse_money(response)

    # 下一页的翻页方式
    def parse_jijing(self, response):
        for data in response.xpath('//*[@class="news_list"]/li'):
            data_url=data.xpath('./a/@href').get()
            data_time=data.xpath('./span/text()').get()
            pagetime=date2time(min_str=data_time)
            yield from over_page(data_url,response,page_num=1,page_time=pagetime,callback=self.parse_detail)

        # 翻页
        page=response.xpath('//a[text()="下一页"]/@href').get()
        response.meta['num'] += 1
        if 'http:' in page:
            yield from over_page(page, response, page_time=pagetime, page_num=response.meta['num'], callback=self.parse_jijing)
        else:
            next_url=f"http://app.finance.china.com.cn{page}"
            yield from over_page(next_url, response, page_time=pagetime, page_num=response.meta['num'],
                                 callback=self.parse_jijing)

    # 遍历url翻页方式
    def parse_baoxian(self, response):
        for url in response.css("li.clearfix h3 a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
            
    def parse_ipo(self,response):
        for url in response.css(".s-list .c h3 a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        
    def parse_money(self,response):
        for url in response.css(".s-list .c h3 a"):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)
    
        next_url = f"{response.meta['next_url']}&page=1"
        print(next_url)
        yield scrapy.Request(next_url, callback=self.parse_next, meta=response.meta)
        
    def parse_next(self,response):
        html=re.findall('\((.*)\)',response.text)
        for ht in html:
            text=json.loads(ht)
            text_=''.join(text)
            xp_html=etree.HTML(text_)
            for li in xp_html.xpath('//*[@class="c"]'):
                url=li.xpath('./h3/a/@href')
                url_=''.join(url)
                yield scrapy.Request(url_,callback=self.parse_detail,meta=response.meta)
        
        response.meta['num']+=1
        next_url=f"{response.meta['next_url']}&page={response.meta['num']}"
        yield from over_page(next_url,response,page_num=response.meta['num']-1,callback=self.parse_next)
            
  

    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_xpath('content_text', '//*[@id="fontzoom"]/p//text()')  # 正文内容/text_content
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@id="source_baidu"]/a/text()')  # 来源/article_source
        item.add_xpath('article_source', '//*[@class="fl time2"]/a/text()')  # 来源/article_source
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

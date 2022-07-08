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



class MydriversComSpider(scrapy.Spider):
    name = 'mydrivers.com'
    allowed_domains = ['mydrivers.com']
    site_name = '快科技'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 资讯中心", "https://news.mydrivers.com/zixun/yitu/index.html"],
        ["企业舆情", "首页 > 科技快讯 > 阿里巴巴", "https://news.mydrivers.com/zixun/alibaba/index.html"],
        ["企业舆情", "首页 > 科技快讯 > 腾讯", "https://news.mydrivers.com/zixun/tencent/index.html"],
        ["企业舆情", "首页 > 科技快讯 > 百度", "https://news.mydrivers.com/zixun/baidu/index.html"],
        ["企业舆情", "首页 > 科技快讯 > 美团", "https://news.mydrivers.com/zixun/meituan/index.html"],
        ["企业舆情", "首页 > 科技快讯 > 谷歌", "https://news.mydrivers.com/zixun/google/index.html"],
        ["企业舆情", "首页 > 科技快讯 > 字节跳动", "https://news.mydrivers.com/zixun/bytedance/index.html"],
        ["企业舆情", "首页 > 科技快讯 > 微软", "https://news.mydrivers.com/zixun/microsoft/index.html"],
        ["企业舆情", "首页 > 科技快讯 > 苹果", "https://news.mydrivers.com/tag/pingguo.htm"],
        ["企业舆情", "首页 > 科技快讯 > 华为", "https://news.mydrivers.com/tag/huawei.htm"],
        ["企业舆情", "首页 > 科技快讯 > 三星", "https://news.mydrivers.com/tag/sanxing.htm"],
        ["企业舆情", "首页 > 科技快讯 > 小米", "https://news.mydrivers.com/tag/xiaomi.htm"],
        ["企业舆情", "首页 > 科技快讯 > OPPO", "https://news.mydrivers.com/tag/oppo.htm"],
        ["企业舆情", "首页 > 科技快讯 > vivo", "https://news.mydrivers.com/tag/vivo.htm"],
        ["企业舆情", "首页 > 科技快讯 > 魅族", "https://news.mydrivers.com/tag/meizu.htm"],
        ["企业舆情", "首页 > 科技快讯 > intel", "https://news.mydrivers.com/tag/intel.htm"],
        ["企业舆情", "首页 > 科技快讯 > AMD", "https://news.mydrivers.com/tag/amd.htm"],
        ["企业舆情", "首页 > 科技快讯 > NVIDIA", "https://news.mydrivers.com/tag/nvidia.htm"],
        ["企业舆情", "首页 > 科技快讯 > 联想", "https://news.mydrivers.com/tag/lianxiang.htm"],
        ["企业舆情", "首页 > 科技快讯 > 七彩虹", "https://news.mydrivers.com/tag/qicaihong.htm"],
        ["企业舆情", "首页 > 科技快讯 > 特斯拉", "https://news.mydrivers.com/tag/tesila.htm"],
        ["企业舆情", "首页 > 科技快讯 > 比亚迪", "https://news.mydrivers.com/tag/biyadi.htm"],
        ["企业舆情", "首页 > 科技快讯 > 小鹏汽车", "https://news.mydrivers.com/tag/xiaopengqiche.htm"],
        ["企业舆情", "首页 > 科技快讯 > 蔚来汽车", "https://news.mydrivers.com/tag/weilaiqiche.htm"],
        ["企业舆情", "首页 > 科技快讯 > 理想汽车", "https://news.mydrivers.com/tag/lixiangqiche.htm"],
        ["企业舆情", "首页 > 科技快讯 > 宝马", "https://news.mydrivers.com/tag/baoma.htm"],
        ["企业舆情", "首页 > 科技快讯 > 奔驰", "https://news.mydrivers.com/tag/benchi.htm"],
        ["企业舆情", "首页 > 科技快讯 > 本田", "https://news.mydrivers.com/tag/bentian.htm"],
        ["企业舆情", "首页 > 科技快讯 > 丰田", "https://news.mydrivers.com/tag/fengtian.htm"]
    ]

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'mydrivers.com/zixun' in response.url:
            code=re.findall('zixun/(.*)/index.html',response.url)
            html_code=''.join(code)
            response.meta['content_list'] = []
            if html_code == 'tencent' or html_code =='microsoft':
                num = 51
            else:
                num = 21
            for i in range(1,num):
                if code == 'yitu':
                    url=f"https://news.mydrivers.com/zixun/getdata.ashx?pageid={i}&action=yitu&nottag=1"
                    yield scrapy.Request(url,callback=self.parse_zixun,meta=response.meta)
                else:
                    url = f"https://news.mydrivers.com/zixun/getdata.ashx?pageid={i}&action={html_code}"
                    yield scrapy.Request(url, callback=self.parse_zixun, meta=response.meta)
            
        elif 'com/tag/' in response.url:
            yield from self.parse_tag(response)

    # 首页>基金
    def parse_tag(self, response):
        for url in response.css(".wnews_lb li h3 a "):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)

        # 翻页
        for page in response.xpath('//a[text()=">"]'):
            yield response.follow(page, meta=response.meta)


    def parse_zixun(self, response):
        for url in response.css("li h3 a"):
            yield response.follow(url, callback=self.content_next, meta=response.meta)
    
    #判断正文是否有分页
    def content_next(self,response):
        content_ = response.xpath('//a[text()="全文"]/@href').getall()
        content_next=''.join(content_)
        if '.htm' in content_next:
            yield response.follow(content_next, callback=self.parse_detail, meta=response.meta)
        else:
            yield from self.parse_detail(response)
            
    
    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_xpath('title', '//*[@class="news_bt"]/text()')
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        item.add_value('content_text', content_rules.extract(response.text))  # 正文内容/text_content
        # 自定义规则
        item.add_xpath('article_source', '//*[@class="news_bt1_left"]/text()',re='出处：(.*) ')  # 来源/article_source
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
        yield item.load_item()

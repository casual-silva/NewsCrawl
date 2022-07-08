# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit

from ..utils import date, over_page
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class CcaonlineCnSpider(scrapy.Spider):
    name = 'ccaonline.cn'
    allowed_domains = ['ccaonline.cn']
    site_name = '中国民用航空网'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["行业舆情", "首页 > 新闻", "http://www.ccaonline.cn/ccanews"],
        ["企业舆情", "首页 > 航企", "http://www.ccaonline.cn/hqtxsy"]
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
        url ='http://www.ccaonline.cn/wp-admin/admin-ajax.php'
        if 'ccaonline.cn/ccanews' in response.url:
            head_data = {"action": "vc_get_vc_grid_data",
                         "tag": "vc_basic_grid",
                         "data[page_id]": "331245",
                         "data[shortcode_id]": "1634115609624-c9bf0128-34c1-4",
                         "_vcnonce": "f4f8fbfc06"}

            news_data = {"action": "vc_get_vc_grid_data",
                         "tag": "vc_basic_grid",
                         "data[page_id]": "331245",
                         "data[shortcode_id]": "1634115609625-eca84bb1-a219-8",
                         "_vcnonce": "f4f8fbfc06"}
            
            yield scrapy.FormRequest(url,callback=self.parse_page,meta=response.meta,formdata=head_data)
            yield scrapy.FormRequest(url, callback=self.parse_page, meta=response.meta, formdata=news_data)
        
        elif '/hqtxsy' in response.url:
            airs_data = {"action": "vc_get_vc_grid_data",
                         "tag": "vc_basic_grid",
                         "data[page_id]": "332735",
                         "data[shortcode_id]": "1641790463940-6f09111d-38cd-5",
                         "_vcnonce": "f4f8fbfc06"}

            news_data = {"action": "vc_get_vc_grid_data",
                         "tag": "vc_basic_grid",
                         "data[page_id]": "332735",
                         "data[shortcode_id]": "1641790463941-5d586834-c9a4-0",
                         "_vcnonce": "f4f8fbfc06"}

            roll_data = {"action": "vc_get_vc_grid_data",
                         "tag": "vc_basic_grid",
                         "data[page_id]": "332735",
                         "data[shortcode_id]": "1641790463942-4839d2b7-baa0-0",
                         "_vcnonce": "f4f8fbfc06"}

            guy_data = {"action": "vc_get_vc_grid_data",
                         "tag": "vc_basic_grid",
                         "data[page_id]": "332735",
                         "data[shortcode_id]": "1641790463942-0c4e0fb2-f0e2-9",
                         "_vcnonce": "f4f8fbfc06"}

            yield scrapy.FormRequest(url, callback=self.parse_page, meta=response.meta, formdata=roll_data)
            yield scrapy.FormRequest(url, callback=self.parse_page, meta=response.meta, formdata=news_data)
            yield scrapy.FormRequest(url, callback=self.parse_page, meta=response.meta, formdata=guy_data)
            yield scrapy.FormRequest(url, callback=self.parse_page, meta=response.meta, formdata=airs_data)
            
        
    def parse_page(self,response):

        for url in response.xpath('//*[@class="vc_gitem-link vc-zone-link"]'):
            yield response.follow(url, callback=self.parse_detail, meta=response.meta)


    def parse_detail(self, response):
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        # 通用提取规则
        content_rules = ContentRules()  # 正文初始化 每次都需要初始化
        item.add_value('title', self.title_rules.extract(response.text))  # 标题/title
        item.add_value('publish_date', self.publish_date_rules.extractor(response.text))  # 发布日期/publish_date
        content=response.xpath('//*[@class="entry-content"]/p//text()|//*[@class="entry-content"]/p//img/@src').getall()
        content_text=[x.strip() for x in content if x.strip() != '']
        item.add_value('content_text', content_text)  # 正文内容/text_content
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

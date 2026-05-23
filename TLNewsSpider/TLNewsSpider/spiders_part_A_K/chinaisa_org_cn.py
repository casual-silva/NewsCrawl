# -*- coding: utf-8 -*-

import re
import math
import scrapy
from urllib.parse import urlsplit
import json
import time
from lxml import etree
from ..utils import date, over_page
from ..items import TlnewsspiderItem, TlnewsItemLoader
from ..package.rules.utils import urljoin
from ..package.rules import TitleRules, PublishDateRules, ContentRules, AuthorExtractor



class ChinaisaOrgCnSpider(scrapy.Spider):
    name = 'chinaisa.org.cn'
    allowed_domains = ['chinaisa.org.cn']
    site_name = '中国钢铁工业协会'
    title_rules = TitleRules()
    publish_date_rules = PublishDateRules()
    author_rules = AuthorExtractor()

    # 分析链接页面之间相似性 分组抓取
    start_urls = [
        ["企业舆情", "首页 > 要闻",
         "http://www.chinaisa.org.cn/gxportal/xfgl/portal/list.html?columnId=c42511ce3f868a515b49668dd250290c80d4dc8930c7e455d0e6e14b8033eae2"],
        ["企业舆情", "首页 > 会员动态",
         "http://www.chinaisa.org.cn/gxportal/xfgl/portal/list.html?columnId=268f86fdf61ac8614f09db38a2d0295253043b03e092c7ff48ab94290296125c"]
    ]
    
    def __init__(self, task_id='', *args, **kwargs):
        super().__init__(*args, **kwargs)  # <- important
        self.task_id = task_id

    def start_requests(self):
        for url_item in self.start_urls:
            classification, catlog, url = url_item
            meta = {'classification': classification}
            yield scrapy.Request(url, callback=self.parse, meta=meta)

    def parse(self, response):
        # 详情页
        if 'columnId=c42511ce3f868a515b49668dd250290c80d4dc8930c7e455d0e6e14b8033eae2' in response.url:
            url='http://www.chinaisa.org.cn/gxportal/xfpt/portal/getColumnList'
            for i in range(1,75):
                t=f"%7B%22columnId%22:%22c42511ce3f868a515b49668dd250290c80d4dc8930c7e455d0e6e14b8033eae2%22,%22param%22:%22%257B%2522pageNo%2522:{i},%2522pageSize%2522:25%257D%22%7D"
                data={'params':t}
                yield from over_page(url, response, callback=self.parse_chinaisa, formdata=data,
                                     page_num=i)
                # yield scrapy.FormRequest(url,callback=self.parse_chinaisa,meta=response.meta,formdata=data)

        if 'columnId=268f86fdf61ac8614f09db38a2d0295253043b03e092c7ff48ab94290296125c' in response.url:
            url = 'http://www.chinaisa.org.cn/gxportal/xfpt/portal/getColumnList'
            for i in range(1, 216):
                t=f"%7B%22columnId%22:%22268f86fdf61ac8614f09db38a2d0295253043b03e092c7ff48ab94290296125c%22,%22param%22:%22%257B%2522pageNo%2522:{i},%2522pageSize%2522:25%257D%22%7D"
                data = {'params': t}
                yield from over_page(url, response, callback=self.parse_chinaisa, formdata=data,
                                     page_num=i)
                # yield scrapy.FormRequest(url, callback=self.parse_chinaisa, meta=response.meta, formdata=data)

    # 首页>基金
    def parse_chinaisa(self, response):
        articleListHtml=json.loads(response.text).get('articleListHtml')
        html=etree.HTML(articleListHtml)
        urls=html.xpath('//*[@class="list"]/li[not(@style)]/a/@href')
        for u in urls:
            response.meta['content_url']=f"http://www.chinaisa.org.cn/gxportal/xfgl/portal/{u}"
            articleId_=re.findall('articleId=(.*)&',u)
            columnId_=re.findall('columnId=(.*)',u)
            articleId=''.join(articleId_)
            columnId=''.join(columnId_)
            url='http://www.chinaisa.org.cn/gxportal/xfpt/portal/viewArticleById'
            t=f"%7B%22articleId%22:%22{articleId}%22,%22columnId%22:%22{columnId}%22%7D"
            data={'params':t}
            yield scrapy.FormRequest(url,callback=self.parse_detail,meta=response.meta,formdata=data)
     
    def parse_detail(self, response):
        article_content = json.loads(response.text).get('article_content')
        article_title=json.loads(response.text).get('article_title')
        html = etree.HTML(article_content)
        content = html.xpath('//*[@class="article_main"]/p//text()')
        content_ = html.xpath('//*[@class="zwcontent"]/p[not(@style)]//text()')
        content_m = html.xpath('//*[@class="MsoNormal"]//text()')
        content_source_=html.xpath('//*[@class="article_title"]/p/text()')
        content_source=''.join(content_source_)
        content_source =content_source.replace('\xa0','')
        publish_date=re.findall('日期：(.*)浏',content_source)
        article_source=re.findall('文章来源：(.*)日',content_source)
        item = TlnewsItemLoader(item=TlnewsspiderItem(), selector=response, response=response)
        item.add_value('title',article_title)  # 标题/title
        item.add_value('publish_date',publish_date)  # 发布日期/publish_date
        if content or content_m == []:
            content_text = [x.strip() for x in content_ if x.strip() != '']
            item.add_value('content_text',content_text)  # 正文内容/text_content
        if content_ or content == []:
            content_text = [x.strip() for x in content_m if x.strip() != '']
            item.add_value('content_text', content_text)  # 正文内容/text_content
        if content_ or content_m == []:
            content_text = [x.strip() for x in content if x.strip() != '']
            item.add_value('content_text', content_text)  # 正文内容/text_content
        item.add_value('article_source',article_source)  # 来源/article_source
        item.add_value('spider_time', date())  # 抓取时间
        item.add_value('created_time', date())  # 更新时间
        item.add_value('source_url', response.meta['content_url'])  # 详情网址/detail_url
        item.add_value('site_name', self.site_name)  # 站点名称
        item.add_value('site_url', urlsplit(response.url).netloc)  # 站点host
        item.add_value('classification', response.meta['classification'])  # 所属分类
        # # 网页源码  调试阶段注释方便查看日志
        item.add_value('html_text', response.text)  # 网页源码
        return item.load_item()

'''
    发布日期
'''

import re

from parsel import Selector
from lxml.html import HtmlElement
from .utils import html2element, config
from .settings import DATETIME_PATTERN, PUBLISH_TIME_META


class PublishDateRules:
    def __init__(self):
        self.time_pattern = DATETIME_PATTERN

    def extractor(self, text, publish_time_xpath: str = '') -> str:
        element = html2element(text) # 转为元素
        publish_time_xpath = publish_time_xpath or config.get('publish_time', {}).get('xpath')
        publish_time = (self.extract_from_user_xpath(publish_time_xpath, element)  # 用户指定的 Xpath 是第一优先级
                        or self.extract_from_meta(element)  # 第二优先级从 Meta 中提取
                        or self.extract_from_text(element))  # 最坏的情况从正文中提取
        return publish_time.strip().strip('\ufeff')

    def extract_from_user_xpath(self, publish_time_xpath: str, element: HtmlElement) -> str:
        if publish_time_xpath:
            publish_time = ''.join(element.xpath(publish_time_xpath))
            return publish_time
        return ''

    def extract_from_text(self, element: HtmlElement) -> str:
        text = ''.join(element.xpath('.//text()'))
        for dt in self.time_pattern:
            dt_obj = re.search(dt, text)
            if dt_obj:
                return dt_obj.group(1)
        else:
            return ''

    def extract_from_meta(self, element: HtmlElement) -> str:
        """
        一些很规范的新闻网站，会把新闻的发布时间放在 META 中，因此应该优先检查 META 数据
        :param element: 网页源代码对应的Dom 树
        :return: str
        """
        for xpath in PUBLISH_TIME_META:
            publish_time = element.xpath(xpath)
            if publish_time:
                return ''.join(publish_time)
        return ''


class PublicationDateRules:

    def __init__(self):
        self.time_rules = PublishDateRules()

    def extract(self, text):

        result = self.template1(text) or self.template2(text) or self.template3(text) or self.template4(text)

        return result

    def template1(self, text):
        '''
        基于这个模板: http://www.gov.cn/zhengce/content/2020-07/10/content_5525614.htm
        :param text: 网页文本
        :return: 发布日期
        '''
        sel = Selector(text=text)
        words = '日期|发布时间'
        re_xpath_var = '.*?'.join(re.split('', words))
        td_sel = sel.xpath('//td//*[re:test(text(), $re_xpath_var)]/..', re_xpath_var=re_xpath_var)
        result = td_sel.xpath('./following-sibling::td/text()').get()
        return result

    def template2(self, text, publish_time_xpath=''):
        '''
        基于这个模板: http://www.gov.cn/zhengce/2020-07/08/content_5525115.htm
        :param text: 网页文本
        :param publish_time_xpath: 时间的xpath路径
        :return: 发布日期
        '''
        element = html2element(text)
        date = self.time_rules.extractor(element, publish_time_xpath=publish_time_xpath)
        return date

    def template3(self, text):
        sel = Selector(text=text)
        words = '日期|发布时间'
        re_xpath_var = '.*?'.join(re.split('', words))
        result = sel.xpath('//span[re:test(text(), $re_xpath_var)]/../text()', re_xpath_var=re_xpath_var).get(default='')
        return result

    def template4(self, text):
        '''
        http://www.miit.gov.cn/n1146295/n1652858/n1652930/n4509607/c8019836/content.html
        :param text:
        :return:
        '''
        sel = Selector(text=text)
        words = '日期|发布时间'
        re_xpath_var = '.*?'.join(re.split('', words))
        result = sel.xpath('//div[re:test(text(), $re_xpath_var)]/text()', re_xpath_var=re_xpath_var).get(default='')
        return result


if __name__ == '__main__':
    pass

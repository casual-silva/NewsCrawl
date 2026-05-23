'''
    相关文档
'''
import re
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor


class RelatedDocumentRules:
    def extract(self, response):
        results = [self.template1(response), self.template2(response)]
        for tem in results:
            if 'http' in tem: # 如果http存在至少说明这是一个网址 增大匹配的准确性
                return tem
        return ''

    def template1(self, response):
        restrict_css = ['.fujian00']
        links = LinkExtractor(restrict_css=restrict_css).extract_links(response)
        return [link.url for link in links]

    def template2(self, response):
        '''
        提取相关链接 这个链接其实在正文里面
        http://www.audit.gov.cn/n5/n25/c136377/content.html
        :param response:
        :return:
        '''
        sel = Selector(response)
        re_xpath_var = '相关链接：'
        result = sel.xpath('//p[re:test(text(), $re_xpath_var)]/./following-sibling::p/a/@href', re_xpath_var=re_xpath_var).get(default='')
        return result


if __name__ == '__main__':
    pass

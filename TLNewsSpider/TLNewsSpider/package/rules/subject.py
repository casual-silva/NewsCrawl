'''
    主题词
'''

import re
from parsel import Selector


class SubjectRules:

    def extract(self, text):
        result = self.template1(text) or self.template2(text) or self.template3(text)
        return result

    def template1(self, text):
        sel = Selector(text=text)
        words = '主题词'
        re_xpath_var = '.*?'.join(re.split('', words))
        td_sel = sel.xpath('//td//*[re:test(text(), $re_xpath_var)]/..', re_xpath_var=re_xpath_var)
        result = td_sel.xpath('./following-sibling::td/text()').get()
        return result

    def template2(self, text):
        sel = Selector(text=text)
        words = '主题词'
        re_xpath_var = '.*?'.join(re.split('', words))
        result = sel.xpath('//span[re:test(text(), $re_xpath_var)]/../text()', re_xpath_var=re_xpath_var).get(default='')
        return result

    def template3(self, text):
        '''
        http://www.miit.gov.cn/n1146295/n1652858/n1652930/n4509607/c8019836/content.html
        :param text:
        :return:
        '''
        sel = Selector(text=text)
        words = '主题词'
        re_xpath_var = '.*?'.join(re.split('', words))
        result = sel.xpath('//div[re:test(text(), $re_xpath_var)]/./following-sibling::div/text()', re_xpath_var=re_xpath_var).get(default='')
        return result

if __name__ == '__main__':
    pass

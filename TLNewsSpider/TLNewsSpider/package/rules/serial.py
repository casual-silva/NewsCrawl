'''
    发文字号
'''

import re
from parsel import Selector


class SerialRules:

    def extract(self, text):
        results = [self.template1(text), self.template2(text), self.template3(text), self.template4(text)]
        for result in results:
            if result.isalnum(): # 判断是否包含数字 一般文号都有数字
                return result
        return ''

    def template1(self, text):
        sel = Selector(text=text)
        words = '文号'
        re_xpath_var = '.*?'.join(re.split('', words))
        td_sel = sel.xpath('//td//*[re:test(text(), $re_xpath_var)]/..', re_xpath_var=re_xpath_var)
        result = td_sel.xpath('./following-sibling::td/text()').get(default='')
        return result

    def template2(self, text):
        sel = Selector(text=text)
        words = '文号'
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
        words = '文号'
        re_xpath_var = '.*?'.join(re.split('', words))
        result = sel.xpath('//div[re:test(text(), $re_xpath_var)]/./following-sibling::div/text()', re_xpath_var=re_xpath_var).get(default='')
        return result

    def template4(self, text):
        '''
        https://www.ndrc.gov.cn/xxgk/zcfb/ghxwj/201712/t20171218_960929.html
        :param text:
        :return:
        '''
        sel = Selector(text=text)
        result = sel.re_first('(.[0-9]{4}.{0,5}\d+号)', default='')
        return result


if __name__ == '__main__':
    pass

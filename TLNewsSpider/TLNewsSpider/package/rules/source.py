'''
    来源
'''
import re
import requests
from parsel import Selector


class SourceRules:

    def extract(self, text):
        selectors = Selector(text=text)
        results = [self.template1(selectors), self.template2(selectors), self.template3(selectors)]
        for result in results:
            if self.is_chinese(result):
                return result
        return ''

    def is_chinese(self, result):
        '''
        看结果中是否包含中文 因为来源绝大部分包含中文 这样提高准确率
        :param result:
        :return:
        '''
        for ch in result:
            if u'\u4e00' <= ch <= u'\u9fff':
                return True
        return False

    def template1(self, selectors):
        '''
        http://www.gov.cn/zhengce/2020-07/08/content_5525115.htm
        :param text:
        :return:
        '''
        words = '来源：.*?'
        word_sel = selectors.xpath('//*[re:test(text(), $re_xpath_var)]', re_xpath_var=words)
        result = word_sel.xpath('string(.)').re_first('来源：(.*)', default='').strip()
        return result

    def template2(self, selectors):
        words = '文章来源'
        re_xpath_var = '.*?'.join(re.split('', words))
        result = selectors.xpath('//div[re:test(text(), $re_xpath_var)]/text()', re_xpath_var=re_xpath_var).get(default='')
        return result

    def template3(self, selectors):
        '''
        http://www.most.gov.cn/kjzc/gjkjzc/nckjyshfz/201706/t20170628_133810.htm 这个来源是渲染出来的 所以位置和源码中不一样
        :param text:
        :return:
        '''
        result = selectors.re_first("var str='(.*?)';", default='')
        return result


if __name__ == '__main__':
    def fetch():
        url = 'http://www.gov.cn/zhengce/2020-06/03/content_5517092.htm'
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.encoding = 'utf-8'
        return response.text
    print(666)
    result = SourceRules().extract(fetch())
    print(result)

'''
    效力
'''

import re
from parsel import Selector


class EffectivenessRules:

    def extract(self, text):
        sel = Selector(text=text)
        words = '效力'
        re_xpath_var = '.*?'.join(re.split('', words))
        td_sel = sel.xpath('//td//*[re:test(text(), $re_xpath_var)]/..', re_xpath_var=re_xpath_var)
        result = td_sel.xpath('./following-sibling::td/text()').get()
        return result


if __name__ == '__main__':
    pass

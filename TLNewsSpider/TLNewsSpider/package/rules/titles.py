'''
    标题
'''

import re
from .utils import config, get_longest_common_sub_string, html2element
from lxml.html import HtmlElement
from .settings import TITLE_HTAG_XPATH, TITLE_SPLIT_CHAR_PATTERN, PUBLISH_TITLE_META


class TitleRules:

    def extract_by_xpath(self, element, title_xpath):
        if title_xpath:
            title_list = element.xpath(title_xpath)
            if title_list:
                return title_list[0]
            else:
                return ''
        return ''

    def extract_by_title(self, element):
        title_list = element.xpath('//title/text()')
        if not title_list:
            return ''
        return title_list[0]
        # title = re.split(TITLE_SPLIT_CHAR_PATTERN, title_list[0])
        # if title:
        #     return title[0]
        # else:
        #     return ''

    def extract_by_htag(self, element):
        title_list = element.xpath(TITLE_HTAG_XPATH)
        if not title_list:
            return ''
        return title_list[0]

    def extract_by_htag_and_title(self, element: HtmlElement) -> str:
        """
        一般来说，我们可以认为 title 中包含新闻标题，但是可能也含有其他文字，例如：
        GNE 成为全球最好的新闻提取模块-今日头条
        新华网：GNE 成为全球最好的新闻提取模块

        同时，新闻的某个 <h>标签中也会包含这个新闻标题。

        因此，通过 h 标签与 title 的文字双向匹配，找到最适合作为新闻标题的字符串。
        但是，需要考虑到 title 与 h 标签中的文字可能均含有特殊符号，因此，不能直接通过
        判断 h 标签中的文字是否在 title 中来判断，这里需要中最长公共子串。
        :param element:
        :return:
        """
        h_tag_texts_list = element.xpath('(//h1//text() | //h2//text() | //h3//text() | //h4//text() | //h5//text())')
        title_text = ''.join(element.xpath('//title/text()'))
        news_title = ''
        for h_tag_text in h_tag_texts_list:
            lcs = get_longest_common_sub_string(title_text, h_tag_text)
            if len(lcs) > len(news_title):
                news_title = lcs
        return news_title

    def extract_by_meta(self, element: HtmlElement) -> str:
        """
        一些很规范的新闻网站，会把新闻的标题放在 META 中，因此应该优先检查 META 数据
        :param element: 网页源代码对应的Dom 树
        :return: str
        """
        for xpath in PUBLISH_TITLE_META:
            publish_title = element.xpath(xpath)
            if publish_title:
                return ''.join(publish_title)
        return ''

    def extract(self, text: str, title_xpath: str = '') -> str:
        element = html2element(text) # 转为元素
        title_xpath = title_xpath or config.get('title', {}).get('xpath')

        title = (self.extract_by_meta(element)
                 or self.extract_by_xpath(element, title_xpath)
                 or self.extract_by_htag_and_title(element)
                 or self.extract_by_title(element)
                 or self.extract_by_htag(element)
                 )
        return title.strip().strip('\ufeff')


if __name__ == '__main__':
    pass

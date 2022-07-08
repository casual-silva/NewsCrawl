import re
from .utils import html2element
from .settings import AUTHOR_PATTERN


class AuthorExtractor:
    def __init__(self):
        self.author_pattern = AUTHOR_PATTERN

    def extractor(self, text: str, author_xpath='', author_css=''):
        element = html2element(text) # 转为元素
        author_xpath = author_xpath
        if author_xpath:
            author = ''.join(element.xpath(author_xpath))
            return author
        text = ''.join(element.xpath('.//text()'))
        for pattern in self.author_pattern:
            author_obj = re.search(pattern, text)
            if author_obj:
                return author_obj.group(1)
        return ''

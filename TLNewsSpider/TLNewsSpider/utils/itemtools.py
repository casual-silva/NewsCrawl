'''

    工具集合

'''
import re


class TakeFirst:
    """
    """

    def __call__(self, values):
        if not isinstance(values, (list, tuple)):
            return values
        for value in values:
            if value is not None and value != '':
                return value


class Strip:
    '''
    Remove the white space characters at the beginning and end of the field
    '''

    def __call__(self, values):
        if isinstance(values, str):
            return values.strip()
        elif isinstance(values, list):
            return [val.strip() for val in values]
        return values


class ReplaceWhiteSpaceCharacter:
    '''
    去掉所有回车、换行、空白符号
    '''

    def __call__(self, values):
        return re.sub("\r|\n|\\s", '', values)


class AuthorOrJournalFilter:
    '''
    作者, 记者：匹配数据简单清洗
    '''
    def __call__(self, values):
        for value in values:
            if value in ('作者', '记者'):
                continue
            if '：' in value:
                value = value.split('：')[-1]
            if value is not None and value != '':
                _values = value.strip('\r').strip('\n').split('\u3000')
                for val in _values:
                    if val in ('作者', '记者'):
                        continue
                    return val
                return value
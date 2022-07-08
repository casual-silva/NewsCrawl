'''
    附件下载
'''

import re
from parsel import Selector
from scrapy.linkextractors import LinkExtractor


class AttachmentDownloadRules:

    def extract(self, response):
        allow = self.allow_extensions() # 允许这些作为附件
        deny_extensions = [
            # 超文本相关
            'htm', 'html', 'shtml', 'css', 'com', 'cn', 'gif'
            # 其他
            'exe', 'bin', 'rss', 'dmg', 'iso', 'apk'] # 不采集的链接扩展名
        restrict_text = ['^(?!.*播放器.*)'] # 不匹配包含某类的文本
        # 在哪里提取链接
        links = LinkExtractor(allow=allow, deny_extensions=deny_extensions, restrict_text=restrict_text).extract_links(response)
        # 返回附件地址以及文字介绍集合
        return [(link.url, link.text) for link in links]

    def allow_extensions(self):
        '''
        返回 IGNORED_EXTENSIONS 中添加了 $ 符号结尾的列表
        该列表作为连接提取器中allow的正则部分，也即是提取以这些结尾的网址 其他的类似 com, cn等结尾的就不需要了
        :return:
        '''
        IGNORED_EXTENSIONS = [
            # archives
            '7z', '7zip', 'bz2', 'rar', 'tar', 'tar.gz', 'zip',

            # images
            'mng', 'pct', 'bmp', 'gif', 'jpg', 'jpeg', 'png', 'pst', 'psp', 'tif',
            'tiff', 'drw', 'dxf', 'eps', 'ps', 'svg', 'cdr', 'ico',

            # audio
            'mp3', 'wma', 'ogg', 'wav', 'ra', 'aac', 'mid', 'au', 'aiff',

            # video
            '3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 'mpg', 'qt', 'swf', 'wmv',
            'm4a', 'm4v', 'flv', 'webm',

            # office suites
            'xls', 'xlsx', 'ppt', 'pptx', 'pps', 'doc', 'docx', 'odt', 'ods', 'odg',
            'odp',

            # other
            'css', 'pdf', 'exe', 'bin', 'rss', 'dmg', 'iso', 'apk', 'ceb'
        ]
        return list(map(lambda x:x+"$", IGNORED_EXTENSIONS))

if __name__ == '__main__':
    print(AttachmentDownloadRules().allow_extensions())

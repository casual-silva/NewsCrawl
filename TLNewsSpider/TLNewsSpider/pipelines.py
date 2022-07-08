# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import logging
from itemadapter import ItemAdapter
from scrapy.exporters import CsvItemExporter
from .utils import date, hash_md5
from .package.database import *
from .package.bloom_redis import BloomFilter

class NewsPreFixPipeline:
    '''
    管道数据存储前数据前处理
    增加 uuid 数据唯一标识,
    uuid: MD5(站点名 + 标题)
    '''
    def process_item(self, item, spider):
        __uuid = item['site_name'] + item['title']
        uuid = hash_md5(__uuid)
        item['uuid'] = uuid
        return item


class NewsFilterPipeline:
    '''
    管道数据过滤 采用redis hash值过滤
    '''
    def process_item(self, item, spider):
        return item


class NewsSaveMysqlPipeline:
    '''
    管道数据过滤 采用redis hash值过滤
    '''
    def open_spider(self, spider):
        self.session = DBSession()

    def process_item(self, item, spider):
        uuid = item['uuid']
        html_text = item['html_text']
        content_text = item['content_text']
        created_time = item['created_time']
        del item['content_text']
        del item['html_text']
        try:
            self.session.add(CeNew(**item))
            self.session.add(CeNewsContent(uuid=uuid, content_text=content_text, created_time=created_time))
            self.session.add(CeNewsHtmlContent(uuid=uuid, html_text=html_text, created_time=created_time))
            self.session.commit()
            logging.info('存储成功 >>> {0} {1} {2}'.format(item['site_name'], item['title'], uuid))
        except Exception as e:
            logging.error("SAVE MYSQL Exception >> {}".format(e))
            self.session.rollback()
            if 'Duplicate entry' not in str(e):
                self.session.rollback()
                raise e
        return item

    def close_spider(self, spider):
        self.session.close()
        pass


class NewsSaveRedisPipeline():
    '''
    记录item数据的source_url至redis 用来去重
    '''
    def __init__(self):
        self.bloom = BloomFilter()

    def process_item(self, item, spider):
        source_url = item['source_url']
        if not self.bloom.isContains(source_url):
            self.bloom.insert(source_url)
            logging.info('写入redis成功：{}'.format(source_url))



class NewsCsvPipeline:

    def open_spider(self, spider):
        file_name = 'news_{}.csv'.format(date('%Y-%m-%d_%H'))
        self.file = open(file_name, 'wb')
        self.csvItemExporter = CsvItemExporter(file=self.file, include_headers_line=True, encoding='gb18030')
        self.csvItemExporter.start_exporting()

    def process_item(self, item, spider):
        self.csvItemExporter.export_item(item)
        return item

    def close_spider(self, spider):
        self.csvItemExporter.finish_exporting()
        self.file.close()
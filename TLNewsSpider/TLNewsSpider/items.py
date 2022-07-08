# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
import scrapy
from .utils.itemtools import *
from itemloaders import ItemLoader
from itemloaders.processors import Compose, MapCompose, Join, Identity


class TlnewsspiderItem(scrapy.Item):
    # define the fields for your item here like:
    uuid = scrapy.Field()
    title = scrapy.Field()
    subtitle = scrapy.Field()
    summary = scrapy.Field()
    author = scrapy.Field()
    site_name = scrapy.Field()
    site_url = scrapy.Field()
    source_url = scrapy.Field()
    article_source = scrapy.Field()
    company_code = scrapy.Field()
    company_name = scrapy.Field()
    publish_date = scrapy.Field()
    spider_time = scrapy.Field()
    created_time = scrapy.Field()
    classification = scrapy.Field()
    html_text = scrapy.Field()
    content_text = scrapy.Field()


class TlnewsItemLoader(ItemLoader):
    default_output_processor = Compose(Strip(), TakeFirst())
    content_text_out = Compose(Strip(), Join(), ReplaceWhiteSpaceCharacter())
    publish_date_out = TakeFirst()
    author_out = AuthorOrJournalFilter()
    title_out = Compose(TakeFirst(), ReplaceWhiteSpaceCharacter())

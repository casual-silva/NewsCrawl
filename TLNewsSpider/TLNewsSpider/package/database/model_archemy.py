# -*- coding: utf-8 -*-

"""
# @Time    : 2022/1/12 0012 14:24
# @Author  : Silva
# @File    : model_archemy.py
"""

'''
# 导出模型文件
sqlacodegen mysql+pymysql://root:HitTuling2019@127.0.0.1:3306/news_crawl > test_model.py
'''

from sqlalchemy import Column, DateTime, String, TIMESTAMP, text
from sqlalchemy.dialects.mysql import TINYINT, INTEGER, LONGTEXT, SMALLINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from TLNewsSpider.config import DB_CONFIG

__ALL__ = ['DBSession', 'CeNew', 'CeNewsHtmlContent', 'CeTaskMotitor', 'CeNewsContent', 'CeTaskSite']

Base = declarative_base()
# 创建的数据库引擎
db_url = "mysql+pymysql://{root}:{pwd}@{host}/{db_name}".format(
    root = DB_CONFIG["MYSQL"]['root'],
    host = DB_CONFIG["MYSQL"]['host'],
    db_name = DB_CONFIG["MYSQL"]['db_name'],
    pwd=quote_plus(DB_CONFIG["MYSQL"]['pwd'])
)
engine = create_engine(db_url)


class CeNew(Base):
    __tablename__ = 'ce_news'

    id = Column(INTEGER(11), primary_key=True)
    uuid = Column(String(64), nullable=False, unique=True, comment='新闻uuid')
    title = Column(String(128), index=True, comment='新闻标题')
    subtitle = Column(String(128), comment='新闻副标题')
    summary = Column(String(128), comment='新闻摘要')
    publish_date = Column(DateTime, index=True, comment='新闻时间')
    company_name = Column(String(16), comment='公司名称')
    company_code = Column(String(16), comment='公司代码')
    site_url = Column(String(32), index=True, comment='站点域名')
    site_name = Column(String(32), comment='站点名称')
    spider_time = Column(DateTime, index=True, comment='创建时间')
    article_source = Column(String(64), comment='文章来源')
    author = Column(String(16), comment='文章作者')
    created_time = Column(DateTime, comment='写入时间')
    classification = Column(String(8), comment='所属分类')
    source_url = Column(String(255), comment='原文链接')
    status = Column(TINYINT(2), nullable=False, server_default=text("'0'"), comment='任务运行状态 0：运行中； 1： 运行完成')
    other = Column(String(255), comment='其他')


class CeNewsContent(Base):
    __tablename__ = 'ce_news_content'

    uuid = Column(String(255), primary_key=True, index=True)
    content_text = Column(LONGTEXT)
    created_time = Column(DateTime)


class CeNewsHtmlContent(Base):
    __tablename__ = 'ce_news_html_content'

    uuid = Column(String(255), primary_key=True, index=True)
    html_text = Column(LONGTEXT)
    created_time = Column(DateTime)


from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
session_factory = sessionmaker(bind=engine)
DBSession  = scoped_session(session_factory)

# data = CeNew(**{'title': '1232131231', 'id': 11 })
# ss = DBSession().add(data)
# print(data.metadata)

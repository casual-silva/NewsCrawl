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

import os

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from urllib.parse import quote_plus
from TLNewsSpider.config import DB_BACKEND, DB_CONFIG, SQLITE_PATH

__ALL__ = ['DBSession', 'CeNew', 'CeNewsHtmlContent', 'CeNewsContent', 'init_database']

Base = declarative_base()


def _build_db_url():
    if DB_BACKEND == 'sqlite':
        sqlite_path = SQLITE_PATH
        if not os.path.isabs(sqlite_path):
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
            sqlite_path = os.path.join(repo_root, sqlite_path)
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        return "sqlite:///{}".format(sqlite_path)

    mysql_config = DB_CONFIG["MYSQL"]
    return "mysql+pymysql://{root}:{pwd}@{host}:{port}/{db_name}?charset=utf8mb4".format(
        root=mysql_config['root'],
        host=mysql_config['host'],
        port=mysql_config.get('port', '3306'),
        db_name=mysql_config['db_name'],
        pwd=quote_plus(mysql_config['pwd'])
    )


engine = create_engine(_build_db_url())


class CeNew(Base):
    __tablename__ = 'ce_news'

    id = Column(Integer, primary_key=True)
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
    status = Column(Integer, nullable=False, server_default=text("'0'"), comment='任务运行状态 0：运行中； 1： 运行完成')
    other = Column(String(255), comment='其他')


class CeNewsContent(Base):
    __tablename__ = 'ce_news_content'

    uuid = Column(String(255), primary_key=True, index=True)
    content_text = Column(Text)
    created_time = Column(DateTime)


class CeNewsHtmlContent(Base):
    __tablename__ = 'ce_news_html_content'

    uuid = Column(String(255), primary_key=True, index=True)
    html_text = Column(Text)
    created_time = Column(DateTime)


from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
session_factory = sessionmaker(bind=engine)
DBSession  = scoped_session(session_factory)


def init_database():
    Base.metadata.create_all(engine)

# data = CeNew(**{'title': '1232131231', 'id': 11 })
# ss = DBSession().add(data)
# print(data.metadata)

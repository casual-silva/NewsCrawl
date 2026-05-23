# -*- coding: utf-8 -*-
import os

"""
# @Time    : 2022/2/17 0017 17:20
# @Author  : Silva
# @File    : config.py
"""

# ------------------ 数据库配置 -------------------------

DB_CONFIG = {
    "MYSQL": {
        "root": os.getenv('NEWSCRAWL_MYSQL_USER', 'root'),
        "host": os.getenv('NEWSCRAWL_MYSQL_HOST', '192.168.1.137'),
        "port": os.getenv('NEWSCRAWL_MYSQL_PORT', '3306'),
        "db_name": os.getenv('NEWSCRAWL_MYSQL_DATABASE', 'news_crawl'),
        "pwd": os.getenv('NEWSCRAWL_MYSQL_PASSWORD', 'Tlrobot123.')
    },
    'REDIS': {
        "host": os.getenv('NEWSCRAWL_REDIS_HOST', '192.168.1.137'),
        "port": os.getenv('NEWSCRAWL_REDIS_PORT', '6379'),
        "db": os.getenv('NEWSCRAWL_REDIS_DB', '2'),
        "password": os.getenv('NEWSCRAWL_REDIS_PASSWORD', '')
    }
}

DB_BACKEND = os.getenv('NEWSCRAWL_DB_BACKEND', 'mysql').lower()
SQLITE_PATH = os.getenv('NEWSCRAWL_SQLITE_PATH', 'data/news_crawl.sqlite3')

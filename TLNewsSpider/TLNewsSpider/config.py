# -*- coding: utf-8 -*-

"""
# @Time    : 2022/2/17 0017 17:20
# @Author  : Silva
# @File    : config.py
"""

# ------------------ 数据库配置 -------------------------

DB_CONFIG = {
    "MYSQL": {
        "root": 'root',
        "host": '192.168.1.137',
        "db_name": 'news_crawl',
        "pwd": 'xxx'
    },
    'REDIS': {
        "host": "192.168.1.137",
        "port": "6379",
        "db": "2",
        "password": ''
    }
}
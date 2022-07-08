# -*- coding: utf-8 -*-

"""
# @Time    : 2022/6/1 0001 15:18
# @Author  : Silva
# @File    : config.py
"""

# 生产者配置

PRODUCER_CONFIG = {
        'bootstrap_servers': '192.168.1.173:9092',
        'client_id': 'touyan',
        'retries': 0,
        'max_request_size': 1048576
    }


# 消费者配置
CONSUMER_CONFIG = {
    'bootstrap_servers': '192.168.1.173:9092',
     'client_id': 'touyan',
     'group_id': None
}
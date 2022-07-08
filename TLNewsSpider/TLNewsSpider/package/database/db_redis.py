# -*- coding: utf-8 -*-

"""
# @Time    : 2022/2/17 0017 16:06
# @Author  : Silva
# @File    : db_redis.py
"""

import redis
from TLNewsSpider.config import DB_CONFIG

__ALL__ = ['redis_client']


class RedisDB:

    def __init__(self):
        try:
            self.__pool = redis.ConnectionPool(**DB_CONFIG['REDIS'])  # redis默认端口是6379
            self._redis = redis.Redis(connection_pool=self.__pool)
        except Exception as e:
            input('Redis Init Error: {0}, {1}'.format(e, **DB_CONFIG['REDIS']))

    # 集合操作
    def sadd(self, key, val):
        return self._redis.sadd(key, val)

    def getbit(self, name, loc):
        return self._redis.getbit(name, loc)

    def setbit(self, name, loc):
        return self._redis.setbit(name, loc, 1)

    def sysmenber(self, key, val):
        return self._redis.sismember(key, val)

    def __del__(self):
        self._redis.close()

redis_client = RedisDB()

# -*- coding: utf-8 -*-

"""
# @Time    : 2022/6/1 0001 14:54
# @Author  : Silva
# @File    : kafaka.py
"""

'''
Note: 
1. 如果消费者如果加了key解码器 key_deserializer 
    当推送过来的消息没有key时会出报错 key：'NoneType' object has no attribute 'decode'
'''

import json
import traceback
from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
# 本地模块
from .utils import JSONEncoder

__all__ = ['kafaka_ctl']

class MyKafaka():

    def __init__(self):
        self.admin = None
        self.producer = None
        self.consumer = None
        # 暂时用print替代log方便后续更改
        self.log = print

    def init_producer(self, **configs):
        '''
        初始化生产者
        '''
        __config = self.common_config(is_produce=True, **configs)
        self.producer = KafkaProducer(**__config)
        self.log('初始化 producer 完成')
        return self.producer

    def init_consumer(self, *topics, **configs):
        '''
        初始化消费者
        '''
        __config = self.common_config(is_produce=False, **configs)
        self.consumer = KafkaConsumer(*topics, **__config)
        return self.consumer

    def init_admin(self, **configs):
        self.admin = KafkaAdminClient(**configs)
        return self.admin

    def common_config(self, is_produce=True, **config):
        serializer = lambda k: json.dumps(k, cls=JSONEncoder).encode()
        deserializer = lambda v: json.loads(v.decode())
        if is_produce:
            __config = {
                'key_serializer': serializer,
                'value_serializer': serializer
            }
        else:
            __config = {
                # 推送过来的消息没有key时 会出报错 key：'NoneType' object has no attribute 'decode'
                # 'key_deserializer': deserializer,
                'value_deserializer': deserializer
            }
        config.update(__config)
        return config

    def send_data(self, topic, value=None, key=None, headers=None, partition=None, timestamp_ms=None):
        self.producer.send(
            topic, value, key, headers, partition, timestamp_ms
        ).add_callback(self.on_send_success).add_errback(self.on_send_error)
        self.producer.flush()

    def on_send_success(self, metadata):
        self.log(f'topic: {metadata.topic} partition: {metadata.partition} offset: {metadata.offset}')

    def on_send_error(self, excp):
        self.log(f'>> ERROR：{excp}')
        self.log(traceback.print_exc())
        raise excp

    def __del__(self):
        if self.producer:
            self.producer.close()
        elif self.consumer:
            self.consumer.close()


kafaka_ctl = MyKafaka()

if __name__ == '__main__':
    # 生产测试
    # kafaka_ctl.init_producer(bootstrap_servers='192.168.1.173:9092')
    # kafaka_ctl.send_data('test', key='test1', value={'val': 222})
    #
    # # 消费者测试
    # consumer = kafaka_ctl.init_consumer('test', bootstrap_servers='192.168.1.173:9092', auto_offset_reset='earliest')
    # for message in consumer:
    #     kafaka_ctl.log("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
    #                                          message.offset, message.key,
    #                                          message.value))
    #
    # 管理端测试
    # admin = kafaka_ctl.init_admin(bootstrap_servers='192.168.1.173:9092')
    # print(admin.list_topics())
    # print(admin.describe_topics(['2022-05-04_topic']))
    # print(admin.delete_topics(['test_ocr']))
    pass

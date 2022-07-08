# -*- coding: utf-8 -*-

"""
# @Time    : 2022/5/11 0011 15:12
# @Author  : Silva
# @File    : spider_proxy.py
"""
import time
import random
import threading
import requests

lock = threading.Lock()
proxy_list = []
expire_time = 10
curent_time = time.time()

proxy_api = None
# bind_api = 'http://www.zdopen.com/ExclusiveProxy/BindIP/?api=202107131051088094&akey=1301638fc3f09b9a&i=1'
# proxy_api = 'http://www.zdopen.com/ExclusiveProxy/GetIP/?api=202107131051088094&akey=1301638fc3f09b9a&count=5&pro=1&order=1&type=3'

def get_proxies():
    '''
    获取第三方代理
    :return: proxy_list
    '''
    def get_web_proxy():
        __list = []
        rsp = requests.get(proxy_api).json()
        for item in rsp['data']['proxy_list']:
            ip_port = "https://{0}:{1}".format(item['ip'], item['port'])
            __list.append(ip_port)
        return __list

    global proxy_list
    global curent_time
    if not proxy_list or time.time() - curent_time > expire_time:
        lock.acquire()
        try:
            proxy_list = get_web_proxy()
        except:
            try:
                time.sleep(1)
                proxy_list = get_web_proxy()
            except Exception as e:
                lock.release()
                print('获取代理出错：{}'.format(e))
                return None
        lock.release()
        curent_time = time.time()
        return random.choice(proxy_list)
    else:
        return random.choice(proxy_list)

if __name__ == '__main__':
    get_proxies()
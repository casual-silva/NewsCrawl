# -*- coding: utf-8 -*-

"""
# @Time    : 2022/6/27 0027 17:02
# @Author  : Silva
# @File    : auto_manage_spiders.py
"""

__DESC__ = '''
基于scrapydweb的公开接口， 批量管理爬虫任务的调度，免去前端页面的单个点击操作
Note：
    1. 操作之前分好可用节点 和 host
'''

import re
import time
import copy
import string
import requests
import argparse
from urllib.parse import urljoin


class BaseInfo:

    def __init__(self, node, host, project_name='TLNewsSpider', version='default: the latest version'):
        self.node = node
        self.node_size = len(host_list) -1
        self.version = version
        self.project_name = project_name
        self.__host = host
        self.host = f'http://{self.__host}/'
        self.api_maps = {
            # 部署新的爬虫版本
            'deploy': '/deploy/upload/',
            # 展示可用的爬虫列表
            'listspiders': f'/api/listspiders/{self.project_name}/{self.version}/',
            # 添加调度任务
            'schedule': '/schedule/run/',
            'check': '/schedule/check/',
            'task': '/tasks/?per_page=1000',
            'job': '/jobs/?per_page=1000',
            'delete_task': '/tasks/xhr/delete/{task_id}/',
            'delete_job': '/jobs/xhr/delete/{job_id}/'
        }
        self.headers = {
            'Host': f'{self.__host}',
            'Origin': f'http://{self.__host}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Referer': f'http://{self.__host}/1/deploy/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
        self.cron_task_params = {
            'action': 'add_fire',
            'task_id': '0',
            'trigger': 'cron',
            'name': '',
            'replace_existing': 'True',
            'year': '*',
            'month': '*',
            'day': '*',
            'week': '*',
            'day_of_week': '*',
            'hour': '*',
            'minute': '0',
            'second': '0',
            'start_date': '',
            'end_date': '',
            'timezone': 'Asia/Shanghai',
            'jitter': '0',
            'misfire_grace_time': '600',
            'coalesce': 'True',
            'max_instances': '1'
        }

    def make_api_url(self, api_name):
        '''
        获取对应的url地址
        '''
        __api_url = self.api_maps[api_name]
        api_url = urljoin(self.host, f"{self.node}{__api_url}")
        return api_url

    def get_latest_timestamp(self):
        return str(int(time.time()))

    def fetch_api(self, url, payload={}, method='POST'):
        '''
        调用接口
        '''
        print(method, 'Fetch: {0}, data: {1}'.format(url, payload))
        if method == 'POST':
            rsp = requests.post(url, data=payload, headers=self.headers)
        else:
            rsp = requests.get(url, params=payload, headers=self.headers)
        try:
            result = rsp.json()
        except:
            result = rsp.text
        return result


class ManageTasks(BaseInfo):

    def __init_api__(self, node, host, project_name='TLNewsSpider', version='default: the latest version'):
        super().__init__(node, host, project_name=project_name, version=version)

    def deploy(self):
        '''
        部署新的爬虫版本
        '''
        deploy_api = self.make_api_url('deploy')
        self.version = self.get_latest_timestamp()
        payload = {
            'folder': self.project_name,
            'project': self.project_name,
            'version': self.version
        }
        self.fetch_api(deploy_api, payload)
        print('部署成功 ', payload)

    def batch_schedule(self, **task_params):
        '''
        批量定时调度
        '''
        all_spider_list = self.listspiders()
        # 根据集群节点数来划分爬虫
        spider_list = self.group_spiders_by_length(all_spider_list, int(self.node), self.node_size)
        for spider in spider_list:
            self.schedule(spider, **task_params)
        print(f'批量调度完成 共 {len(spider_list)} 条')

    def schedule(self, spider='', **task_paramas):
        '''
        单次调度任务： 调度之前必须执行检查操作：check_cmd
        '''
        # 检查
        self.check_cmd(spider, **task_paramas)
        # 调度
        schedule_api = self.make_api_url('schedule')
        trans_spider_name = spider.replace('.', '-')
        trana_version = self.version.replace(': ', '-').replace(' ', '-')
        payload = {'filename': f'{self.project_name}_{trana_version}_{trans_spider_name}.pickle'}
        result = self.fetch_api(schedule_api, payload)
        return result

    def check_cmd(self, spider, **task_paramas):
        '''
        检查shedule命令
        目的是 scrapyd_web_manager 服务内部会缓存记录
        调度时的一些信息从slot中获取
        '''
        check_api = self.make_api_url('check')
        payload = {
            'project': self.project_name,
            '_version': self.version,
            'spider': spider,
        }
        if task_paramas:
            cron_task_params = copy.deepcopy(self.cron_task_params)
            cron_task_params.update(task_paramas)
            payload.update(cron_task_params)
        result = self.fetch_api(check_api, payload)
        print("检查完毕：", result)

    def batch_stop_job(self):
        '''
        停止所有正在运行中的任务
        '''
        task_api = self.make_api_url('job')
        result = self.fetch_api(task_api, method='GET')
        # 匹配出所有任务对应的 stop_api
        url_actions = re.findall("url_action: '(.*?)',", result, re.S)
        stop_task_urls = [urljoin(self.host, url) for url in url_actions if 'stop' in url]
        for stop_task_url in stop_task_urls:
            self.fetch_api(stop_task_url)
        print(f'停止所有任务完毕：共 {len(stop_task_urls)} 条')

    def batch_delete_task(self):
        '''
        清空首页所有定时任务, 第一次执行是停止，第二次是删除记录
        '''
        task_api = self.make_api_url('task')
        result = self.fetch_api(task_api)
        # 匹配出所有任务对应的 delete_api
        url_actions = re.findall("url_action: '(.*?)',", result, re.S)
        delete_task_urls = [urljoin(self.host, url) for url in url_actions]
        for delete_task_url in delete_task_urls:
            self.delete_task(delete_task_url=delete_task_url)
        print(f'清空定时任务完毕：共 {len(delete_task_urls)} 条')

    def batch_delete_job(self):
        '''
        清空首页所有job任务, 未停止的任务不能删除
        '''
        task_api = self.make_api_url('job')
        result = self.fetch_api(task_api, method='GET')
        # 匹配出所有任务对应的 delete_api
        url_deletes = re.findall("url_delete: '(.*?)',", result, re.S)
        delete_job_urls = [urljoin(self.host, url) for url in url_deletes]
        for delete_job_url in delete_job_urls:
            self.delete_job(delete_job_url=delete_job_url)
        print(f'清空所有任务完毕: 共 {len(delete_job_urls)} 条')

    def delete_task(self, delete_task_url=None, task_id=None):
        '''
        删除指定定时任务
        '''
        if not delete_task_url and task_id:
            delete_task_url = self.make_api_url('delete_task').format(task_id=task_id)
        if not delete_task_url:
            raise Exception('delete_task 参数为空')
        return self.fetch_api(delete_task_url)

    def delete_job(self, delete_job_url=None, job_id=None):
        '''
        删除指定job的记录
        '''
        if not delete_job_url and job_id:
            delete_job_url = self.make_api_url('delete_job').format(job_id=job_id)
        if not delete_job_url:
            raise Exception('delete_job 参数为空')
        return self.fetch_api(delete_job_url)

    def listspiders(self):
        '''
        指定版本的spider列表
        '''
        listspiders_api = self.make_api_url('listspiders')
        result = self.fetch_api(listspiders_api)
        spiders_list = result.get('spiders', [])
        return spiders_list

    def group_spiders_by_chars(self, spiders_list, node, node_size):
        '''
        通过首字母等分爬虫
        '''
        # chars = [str(i) for i in range(10)]
        # chars.extend(list(string.ascii_lowercase))
        chars = list(string.ascii_lowercase)
        shard_chars = self.group_spiders_by_length(chars, node, node_size)
        shard_spiders = []
        for spider_name in spiders_list:
            if spider_name[0] in shard_chars:
                shard_spiders.append(spider_name)
        print(f'当前节点分组区间为：{shard_chars[0]} - {shard_chars[-1]}')
        return shard_spiders

    def group_spiders_by_length(self, spiders_list, node, node_size):
        '''
        通过爬虫长度等分
        '''
        if node > node_size:
            raise Exception('group_spiders_by_length：超出界限')
        # 总爬虫数
        spider_size = len(spiders_list)
        # 分片长度
        shard_len = spider_size // node_size
        # 当前分片起始位置
        start = shard_len * (node - 1)
        end = spider_size + 1 if node_size == node else node * shard_len
        print(f'单前节点分组数为：{end - start}')
        return spiders_list[start : end]


def parse_args():
    parser = argparse.ArgumentParser(description=__DESC__)
    # 主节点
    parser.add_argument("-host", "--host", default='192.168.167.85:5000', help='host: 当前集群主机节点')
    # 当前可用集群节点
    parser.add_argument("-n", "--node", choices=['1', '2'], default='1', help='node: 当前可用的集群节点索引')
    # 是否使用定时任务
    parser.add_argument("-t", "--time", choices=[0, 1, 2], type=int, default=0, help='定时任务类型选择(小时) 0: 不定时')
    # 部署版本
    parser.add_argument("-dp", "--deploy", action='store_true', help='deploy: 部署最的爬虫版本')
    # 调度任务
    parser.add_argument("-bsd", "--batch_schedule", action='store_true', help='batch_schedule: 一键调度所有爬虫')
    # 终止任务
    parser.add_argument("-bst", "--batch_stop_job", action='store_true', help='batch_stop_job: 一键停止所有爬虫')
    # 删除
    parser.add_argument("-bdt", "--batch_delete_task", action='store_true', help='batch_delete_task: 一键删除所有cron定时任务')
    parser.add_argument("-bdj", "--batch_delete_job", action='store_true', help='batch_delete_job: 一键删除所有任务')
    # 查看爬虫列表
    parser.add_argument("-ls", "--listspiders", action='store_true', help='listspiders: 查看所有爬虫名')
    return parser.parse_args()

#  -----------------配置参数-------------------------
cron_list = [None, '2,10', '8']
# 当前集群节点信息展示
host_list = ['占位', '192.168.167.84:5000', '192.168.167.85:5000']


def main():
    args = parse_args()
    # 初始化管理对象
    mng = ManageTasks(args.node, args.host)
    for func_name, val in args.__dict__.items():
        if val is not True:
            continue
        print(func_name, val)
        func = getattr(mng, func_name)
        # ------------------指定定时任务参数-----------------------
        if func_name == 'batch_schedule':
            if args.time == 0:
                func()
            else:
                func(hour=cron_list[args.time])
        else:
            result = func()
            if func_name == 'listspiders':
                print(result)


if __name__ == '__main__':
    main()

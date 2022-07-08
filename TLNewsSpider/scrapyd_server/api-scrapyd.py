
__doc__ = ''' Scrapy Api 命令查询'''

__author__ = 'silva'

import os
import json
import requests
import argparse
from urllib.parse import urljoin

headers = {}

host = ''

current_dir = os.path.abspath(os.path.dirname(__file__))

# function map with api
api_path = {
    'cancel': 'cancel.json',
    'schedule': 'schedule.json',
    'listjobs': 'listjobs.json',
    'status': 'listprojects.json',
    'addversion': 'addversion.json',
    'delversion': 'delversion.json',
    'delproject': 'delproject.json',
    'listspiders': 'listspiders.json',
    'listprojects': 'listprojects.json',
    'listversions': 'listversions.json',
}

class Method(object):

    headers = headers

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def status(self):
        _path = api_path[self.kwargs['action']]
        return self._fetch(_path)

    def addversion(self):
        _path = api_path[self.kwargs['action']]
        project = self.kwargs.get('project')
        version = self.kwargs.get('version')
        egg_name = self.kwargs.get('egg') + '.egg'
        egg_path = os.path.join(current_dir, 'eggs', project, egg_name)
        with open(egg_path, 'rb') as fp:
            content = fp.read()
            return self._fetch(_path, method="POST", project=project, egg=content, version=version)

    def schedule(self):
        _path = api_path[self.kwargs['action']]
        project = self.kwargs.get('project')
        spiders = self.kwargs.get('spider')
        addjob_list = []
        for spider in spiders:
            rsp = self._fetch(_path, method="POST", project=project, spider=spider)
            addjob_list.append(json.loads(rsp.text))
        return json.dumps(addjob_list)

    def cancel(self):
        # 待测试
        _path = api_path[self.kwargs['action']]
        project = self.kwargs.get('project')
        jobs = self.kwargs.get('job')
        deljob_list = []
        for job in jobs:
            rsp =  self._fetch(_path, method="POST", project=project, job=job)
            deljob_list.append(json.loads(rsp.text))
        return json.dumps(deljob_list)

    def listprojects(self):
        _path = api_path[self.kwargs['action']]
        return self._fetch(_path)

    def listversions(self):
        _path = api_path[self.kwargs['action']]
        project = self.kwargs.get('project')
        return self._fetch(_path, project=project)

    def listspiders(self):
        _path = api_path[self.kwargs['action']]
        project = self.kwargs.get('project')
        _version = self.kwargs.get('version')
        if _version:
            return self._fetch(_path, project=project, _version=_version)
        return self._fetch(_path, project=project)

    def listjobs(self):
        _path = api_path[self.kwargs['action']]
        project = self.kwargs.get('project')
        return self._fetch(_path, project=project)

    def delversion(self):
        _path = api_path[self.kwargs['action']]
        project = self.kwargs.get('project')
        version = self.kwargs.get('version')
        return self._fetch(_path, method="POST", project=project, version=version)

    def delproject(self):
        _path = api_path[self.kwargs['action']]
        project = self.kwargs.get('project')
        return self._fetch(_path, method="POST", project=project)

    def _fetch(self, path, method='GET', **kwargs):
        '''
        返回响应对象
        '''
        url = urljoin(host, path)
        if self.kwargs.get('headers'):
            self.headers = kwargs.get('headers')
        if method == 'GET':
            rsp = requests.get(url, params=kwargs, headers=self.headers)
        else:
            rsp = requests.post(url, data=kwargs, headers=self.headers)
        return rsp


class ScrapyApp(object):

    def __init__(self, **kwargs):
        self._init_args(**kwargs)
        # 运行指定方法
        opt = getattr(Method(**kwargs), self.action)()
        # 查询结果
        if opt:
            print('opt:', opt.text)
            if isinstance(opt, str):
                print('RESULT:', json.dumps(json.loads(opt), indent=1))
            else:
                print('API:', opt.url)
                print('RESULT:', json.dumps(json.loads(opt.text), indent=1))
        else:
            print('API 查询出错!')

    def _init_args(self, **kwargs):
        self.action = kwargs.get('action')

def main():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-h', '--help', dest='help', help='获取帮助信息', action='store_true', default=False)
    # 通用参数
    parser.add_argument('-p', '--project', dest='project', help='项目名')
    parser.add_argument('-v', '--version', dest='version', help='版本名')
    parser.add_argument('-e', '--egg', dest='egg', help='项目打包文件名, 不加后缀')
    parser.add_argument('-j', '--job', dest='job', nargs='+', help='调度中的job id')
    parser.add_argument('-s', '--spider', dest='spider', nargs='+', help='指定spider名称 (可多选)')
    # 服务配置
    parser.add_argument('-server', '--server', dest='server', default='127.0.0.1', help='服务地址 默认: localhost')
    parser.add_argument('-port', '--port', dest='port', default=6800, help='指定端口 默认: 6800')
    # 执行动作分组
    action_option = parser.add_argument_group()
    action_option.add_argument('-status', '--status', dest='action', action='store_const', const='status', help='检查服务运行状态  >> 示例：-status')
    action_option.add_argument('-sd', '--schedule', dest='action', action='store_const', const='schedule', help='schedule 添加调度任务 >> 示例：-sd -p GovSpider -s jl.gov sh.gov -v 001')
    action_option.add_argument('-av', '--addversion', dest='action',action='store_const', const='addversion',  help='给项目添加版本号, 不存在则创建项目 >> 示例：-av -p Silva -v 001 -egg 001')
    action_option.add_argument('-c', '--cancel', dest='action',action='store_const', const='cancel', help='移除调度中的spider任务 示例：-c -p GovSpider -j 2edf71 04db14c')
    action_option.add_argument('-lp', '--listprojects', dest='action',action='store_const', const='listprojects', help='打印已经部署的项目列表 >> 示例：-lp ')
    action_option.add_argument('-lv', '--listversions', dest='action',action='store_const', const='listversions', help='打印指定项目的版本列表 >> 示例：-lv -p GovSpider')
    action_option.add_argument('-ls', '--listspiders', dest='action',action='store_const', const='listspiders', help='打印项目版本下的spiders, (_version可选, 默认为最新版本) >> 示例：-ls -p GovSpider -v 001')
    action_option.add_argument('-lj', '--listjobs', dest='action',action='store_const', const='listjobs', help='打印项目中spider运行详情信息 >> 示例：-lj -p GovSpider')
    action_option.add_argument('-dv', '--delversion', dest='action',action='store_const', const='delversion', help='删除已打包的版本 >> 示例：-dv -p GovSpider -v 001')
    action_option.add_argument('-dp', '--delproject', dest='action',action='store_const', const='delproject', help='删除已创建的项目 >> 示例：-dp -p GovSpider')

    # 详情参数分组
    args = parser.parse_args()
    if args.help:
        parser.print_help()
    elif args.action:
        global host
        host = 'http://{0}:{1}/'.format(args.server, args.port)
        print('查询服务地址：{}'.format(host))
        ScrapyApp(**args.__dict__)
    else:
        parser.print_usage()

if __name__ == '__main__':
    main()
    # 测试
    # host = 'http://127.0.0.1:6800/'
    # data = Method(project='GovPolicySpider', action='listjobs').listjobs()
    # print(json.dumps(json.loads(data.text), indent=1))

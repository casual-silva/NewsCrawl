# TLNewsSpider-舆情信息获取

# 一、项目介绍

可视化舆情信息获取平台: 基于GNE通用文本抽取模块提取文章所需信息, 目前包含大约300多个舆情站点

# 二、技术组成

主干技术：python、scrapy、scrapyd、scrapydweb(开源管理平台)、mysql、redis

爬虫可配置中间件：

- redis去重中间件
- 请求重试中间件
- 代理中间件
- 爬虫详情信息定时推送至第三方小程序（微信、飞书等）

爬虫可配置数据管道：

- 数据前处理
- 数据过滤清洗
- 数据存储入库
- 数据入redis（同redis去重）

脚本：

- 数据推送至 Kafaka

其他scrapy高级功能

# 三、安装部署

> 需上传项目至服务器固定目录： /home/spider_workplace/

## 1、安装Docker、 Docker-Compose

### 1.1、在线安装docker (centos 系统)

**sudo权限下** 

```bash
yum update 
yum install -y yum-utils
yum install docker
# 使用国内镜像仓库
curl -sSL https://get.daocloud.io/daotools/set_mirror.sh | sh -s https://registry.docker-cn.com
# 重启
systemctl restart docker
# 启动测试
docker run hello-world
```

### 1.2、离线安装docker 

参考： https://blog.csdn.net/xinle0320/article/details/124205608

### 1.3、在线安装docker-compose

```bash
curl -L "https://github.com/docker/compose/releases/download/1.25.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
# 添加权限
chmod +x /usr/local/bin/docker-compose
```

### 1.4、离线安装

1. github 离线下载对应版本 docker-compose

> https://github.com/docker/compose/releases/download/{version}/docker-compose-linux-x86_64

2. 上传至服务目录:  /usr/local/bin/docker-compose
3. 修改权限：chmod +x /usr/local/bin/docker-compose

## 2、安装数据库

```bash
1. 添加需要初始化的数据库 sql 表结构文件 > 重命名init.sql 上传
# 数据库存储目录
mv ./docker_yml/database  /data/ && cd /data/database
# 安装启动
docker-compose up -d
# 检查是否启动成功
docker-compose ps
```

## 3、安装scrapyd、scrapydweb、logparser

```bash
cd ./docker_yml/news_crawl 
# 安装启动
docker-compose up -d
# 检查是否启动成功
docker-compose ps
# 启动失败参考: 4、修改scrapydweb 配置、添加集群等
```

## 4、修改scrapydweb 配置、添加集群等

```bash
# 根据报错或者其他需求修改 scrapydweb_settings_v10.py 配置文件
vim /home/spider_workplace/TLNewsCrawl/TLNewsSpider/scrapyd_web_manager/scrapydweb_settings_v10.py
# 重建容器
docker-compose down
docker-compose up -d
# 查看日志：
docker-compose logs
```

# 四、任务调度

### 1. 使用介绍

基于scrapydweb的公开接口， 批量管理爬虫任务的调度，免去前端页面的单个点击操作 Note： 1. 操作之前分好可用节点 和 host
集群模式下**<u>多个节点爬虫任务数量的划分策略</u>**有两种: 

- def: group_spiders_by_chars 通过首字母等分爬虫 
- def: group_spiders_by_length 通过爬虫数量等分 **(目前使用的这种)**

```bash
>> python auto_manage_spiders.py -h

usage: auto_manage_spiders.py [-h] [-host HOST] [-n {1,2}] [-t {0,1,2}] [-dp]
                              [-bsd] [-bst] [-bdt] [-bdj] [-ls]
基于scrapydweb的公开接口， 批量管理爬虫任务的调度，免去前端页面的单个点击操作 Note： 1. 操作之前分好可用节点 和 host

optional arguments:
  -h, --help            show this help message and exit
  -host HOST, --host HOST
                        host: 当前集群主机节点
  -n {1,2}, --node {1,2}
                        node: 当前可用的集群节点索引
  -t {0,1,2}, --time {0,1,2}
                        定时任务类型选择(小时) 0: 不定时
  -dp, --deploy         deploy: 部署最的爬虫版本
  -bsd, --batch_schedule
                        batch_schedule: 一键调度所有爬虫
  -bst, --batch_stop_job
                        batch_stop_job: 一键停止所有爬虫
  -bdt, --batch_delete_task
                        batch_delete_task: 一键删除所有cron定时任务
  -bdj, --batch_delete_job
                        batch_delete_job: 一键删除所有任务
  -ls, --listspiders    listspiders: 查看所有爬虫名
```

### 2. 使用示例

**NOTE：提示**

1. 在网络互通的条件下任意位置执行该脚本；否则在容器内执行。

2. --host 参数默认值设置为当前主节点 **（必要）**

3. host_list: 列表加上当前所有节点 host **（必要）**

4. cron_list: 按需求设置定时任务需要的cron参数 -- 当前为按小时定时，有需要可自行修改 **(非必要)**

   

```python
# 批量启动节点1的爬虫
python auto_manage_spiders.py -n 1

# 批量启动节点2的爬虫、同时添加到定时任务
python auto_manage_spiders.py -n 2 -t 1

# 部署新的爬虫版本
python auto_manage_spiders.py -dp
```


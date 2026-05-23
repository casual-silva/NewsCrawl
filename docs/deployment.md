# NewsCrawl 部署启动方案

本文档说明当前项目的启动复杂度、推荐启动方式，以及根目录 `start.sh` 的一键式部署用法。

## 1. 当前启动方式分析

原始部署方式把数据库、Redis、scrapyd、scrapydweb 拆成多个目录和多段命令：

- 数据库需要先进入 `docker_yml/database`，启动 MySQL 和 Redis。
- 爬虫调度服务需要再进入 `docker_yml/news_crawl`，启动 scrapyd、scrapydweb、logparser。
- scrapydweb 配置中存在固定机器路径和固定 MySQL 地址，换机器后容易启动失败。
- 本地只想快速验证项目时，也必须准备 MySQL/Redis，启动成本偏高。

结论：完整生产部署可以保留 Docker Compose，但日常开发和快速验证不应该强依赖 MySQL/Redis。当前已经通过环境变量支持 SQLite、本地数据目录和动态项目路径，入口统一收敛到根目录 `start.sh`。

## 2. 快速启动

适合本地开发、功能验证、临时部署演示。该模式会自动创建 Python 虚拟环境，安装依赖，使用 SQLite 替代 MySQL，并关闭 Redis 去重依赖。

```bash
./start.sh quick
```

启动成功后访问：

- scrapyd: http://127.0.0.1:6800
- scrapydweb: http://127.0.0.1:5000

快速启动的默认数据位置：

- 新闻 SQLite：`data/news_crawl.sqlite3`
- scrapydweb 数据：`data/scrapydweb`
- 服务日志：`logs/scrapyd.log`、`logs/scrapydweb.log`

常用环境变量：

```bash
# 自定义 SQLite 文件路径
NEWSCRAWL_SQLITE_PATH=/tmp/news_crawl.sqlite3 ./start.sh quick

# 已经装过依赖时跳过 pip 安装
NEWSCRAWL_INSTALL_DEPS=0 ./start.sh quick

# 使用指定 Python 创建虚拟环境
PYTHON_BIN=/usr/bin/python3 ./start.sh quick
```

## 3. 完整部署启动

适合服务器部署或接近生产的完整联调。该模式使用 Docker Compose 一次性启动 MySQL、Redis、scrapyd、scrapydweb 和 logparser。

```bash
./start.sh full
```

完整部署默认暴露端口：

- MySQL: `3306`
- Redis: `6379`
- scrapyd: `6800`
- scrapydweb: `5000`

可配置 MySQL root 密码：

```bash
NEWSCRAWL_MYSQL_PASSWORD='your-password' ./start.sh full
```

完整部署使用的 Compose 文件：

- `docker_yml/database/docker-compose.yml`
- `docker_yml/news_crawl/docker-compose.yml`

`start.sh full` 会自动准备 MySQL/Redis 挂载目录，并通过 `NEWSCRAWL_ROOT` 把当前仓库挂载进容器，不再要求项目必须放在固定的 `/home/spider_workplace/`。

## 4. 服务管理命令

```bash
# 查看服务健康状态
./start.sh status

# 查看日志
./start.sh logs scrapyd
./start.sh logs scrapydweb
./start.sh logs docker

# 停止 quick/full 启动的服务
./start.sh stop
```

## 5. 常见问题

### 依赖安装卡在 demjson

项目依赖中有 `demjson==2.2.4`，该包不兼容新版 setuptools 的默认构建方式。`start.sh` 已经固定 `setuptools<58`，并使用兼容参数安装 requirements。

### scrapydweb 提示项目目录不存在

旧配置写死了 Windows 路径。当前配置会优先读取：

- `NEWSCRAWL_ROOT`
- `NEWSCRAWL_SCRAPY_PROJECTS_DIR`

不设置时默认使用当前仓库根目录。

### 没有 MySQL 或 Redis

使用快速启动：

```bash
./start.sh quick
```

该模式使用 SQLite 存储新闻数据和 scrapydweb 数据，并关闭 Redis 相关中间件和管道。

### Docker Compose 命令差异

脚本会优先使用 `docker compose`，如果不存在则尝试 `docker-compose`。两者都不存在时，`full` 模式会直接报错。

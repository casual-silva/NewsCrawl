# Scrapy settings for TLNewsSpider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import datetime
import time

BOT_NAME = 'TLNewsSpider'

SPIDER_MODULES = ['TLNewsSpider.spiders_part_A_K', 'TLNewsSpider.spiders_part_L_Z']

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'TLNewsSpider (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs

DOWNLOAD_DELAY = 0.5
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 8

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.62 Safari/537.36",
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
   # 'TLNewsSpider.middlewares.TlnewsspiderSpiderMiddleware': 543,
}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    # redis去重中间件
    'TLNewsSpider.middlewares.TlnewsspiderDownloaderMiddleware': 543
    # 重试 | 代理中间件
    # 'TLNewsSpider.middlewares.MyRetryMiddleware': 544,
}


# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    # item 前处理 格式化
    # 'TLNewsSpider.pipelines.NewsPreFixPipeline': 100,
    # item 过滤清洗中间件
    # 'TLNewsSpider.pipelines.NewsFilterPipeline': 200,
    # item mysql入库
    # 'TLNewsSpider.pipelines.NewsSaveMysqlPipeline': 300,
    # item redis记录
    # 'TLNewsSpider.pipelines.NewsSaveRedisPipeline': 400,
}


# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings

# HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'


# 自定义 genspider 模板文件
TEMPLATES_DIR = 'TLNewsSpider/templates'

# 附件存储
# FILES_STORE = '.'

################################ Spidermon ###################################
SPIDERMON_ENABLED = False  # 开启Spidermon监控

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html

# EXTENSIONS = {
    # "spidermon.contrib.scrapy.extensions.Spidermon": 500  # 指定扩展位置以及启动顺序
# }

# SPIDERMON_SPIDER_CLOSE_MONITORS = [
#     "TLNewsSpider.package.monitors.monitors.SpiderCloseMonitorSuite",  # 指定爬虫关闭之时执行的爬虫监控方案
# ]
#
# SPIDERMON_PERIODIC_MONITORS = {
#     "TLNewsSpider.package.monitors.monitors.PeriodicMonitorSuite": 60  # Every xx seconds
# }

################################ Scrapy-Selenium ###################################
from shutil import which

SELENIUM_DRIVER_NAME = 'firefox'
SELENIUM_DRIVER_EXECUTABLE_PATH = which('geckodriver')
SELENIUM_DRIVER_ARGUMENTS = []  # '--headless' if using chrome instead of firefox
SELENIUM_DRIVER_PROFILES = {
    'network.proxy.type': 4,
    'dom.webdriver.enabled': False,
    'useAutomationExtension': False,
    'browser.cache.disk.enable': False,
    'browser.cache.memory.enable': False,
    'browser.cache.offline.enable': False,
    'network.http.use-cache': False,
}

################################ 日志 ###################################
# import logging
# LOG_LEVEL = 'DEBUG'
# to_day = datetime.datetime.now()
# LOG_FILE = 'log/scrapy_{}_{}_{}_{}.log'.format(to_day.year, to_day.month, to_day.day, to_day.minute)
#
# # 控制台打印输出日志
# console = logging.StreamHandler()  # 定义一个StreamHandler，将INFO级别或更高的日志信息打印到标准错误，并将其添加到当前的日志处理对象
# console.setLevel(logging.INFO)  # 设置要打印日志的等级，低于这一等级，不会打印
# # formatter = logging.Formatter("%(asctime)s - %(levelname)s: %(message)s")
# # console.setFormatter(formatter)
# logging.getLogger().addHandler(console)

###########################是否限制翻页数#######################################
PAGE_LIMIT = 100  # 限制最多翻页[n]页， [-n]小于0为不限制
TIME_LIMIT= 30 # 限制时间[n]天， [0]为不限制,

###########################kafka参数设置#######################################
# interval_time_min = 60  # 设置推送数据的间隔时间       单位：分钟
# num = 200    			# 设置每一次间隔推送的数量     单位：条

########################### 代理配置信息 #######################################
# 使用站大爷-独享IP池 代理套餐
PROXY_API = 'http://www.zdopen.com/ExclusiveProxy/GetIP/?api=202107131051088094&akey=1301638fc3f09b9a&count=5&pro=1&order=1&type=3'
BIND_PROXY_API = 'http://www.zdopen.com/ExclusiveProxy/BindIP/?api=202107131051088094&akey=1301638fc3f09b9a&i=1'

# # 重试配置参数
# RETRY_TIMES = 3
# RETRY_ENABLED = True
# RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429, 302]
# HTTPERROR_ALLOWED_CODES = [301, 302]

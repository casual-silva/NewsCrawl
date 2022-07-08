import datetime
import json
import re
import time


def trans_str(strs=''):
    '''
    excel 表格内的 "数据类别 位置 爬取模块" 信息复制后转化为列表形式
    :strs
        企业舆情	首页 > 基金	https://fund.stockstar.com
        企业舆情	首页 - 保险 - 行业公司	http://stock.hexun.com/dongtai/
    :return
        [["企业舆情", "首页 > 基金", "https://fund.stockstar.com"],
        ["企业舆情", "首页 > 保险 > 行业动态", "http://stock.hexun.com/dongtai/"]]
    '''
    val_list = []
    for item in strs.split('\n'):
        val_list.append([val.strip() for val in item.split('\t')])
    result = json.dumps(val_list, ensure_ascii=False).replace('],', '],\n')
    print(result)


def getTimeStamp(date):
    result = re.search(r"[\-\+]\d+", date)
    if result:
        time_area = result.group()
        symbol = time_area[0]
        offset = int(time_area[1]) + int(time_area[2])
        if symbol == "+":
            format_str = '%a, %d %b %Y %H:%M:%S ' + time_area
            if "UTC" in date:
                format_str = '%a, %d %b %Y %H:%M:%S ' + time_area + ' (UTC)'
            if "GMT" in date:
                format_str = '%a, %d %b %Y %H:%M:%S ' + time_area + ' (GMT)'
            if "CST" in date:
                format_str = '%a, %d %b %Y %H:%M:%S ' + time_area + ' (CST)'
            utcdatetime = time.strptime(date, format_str)
            tempsTime = time.mktime(utcdatetime)
            tempsTime = datetime.datetime.fromtimestamp(tempsTime)
            if offset > 8:
                offset = offset - 8
                tempsTime = tempsTime + datetime.timedelta(hours=offset)
                localtimestamp = tempsTime.strftime("%Y-%m-%d")
            else:
                format_str = '%a, %d %b %Y %H:%M:%S ' + time_area
                utcdatetime = time.strptime(date, format_str)
                tempsTime = time.mktime(utcdatetime)
                tempsTime = datetime.datetime.fromtimestamp(tempsTime)
                tempsTime = tempsTime + datetime.timedelta(hours=(offset + 8))
                localtimestamp = tempsTime.strftime("%Y-%m-%d")
            return localtimestamp


def date2time(date_str=None, time_str=None):
    if date_str:
        time_struct = time.strptime(date_str, "%Y-%m-%d")
    if time_str:
        time_struct = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    time_stamp = time.mktime(time_struct)
    return time_stamp


if __name__ == '__main__':
    result = trans_str('''行业舆情	首页 > 行业资讯 > 国内新闻	http://www.csia.net.cn/Article/ShowClass.asp?ClassID=7
行业舆情	首页 > 行业资讯 > 国际新闻	http://www.csia.net.cn/Article/ShowClass.asp?ClassID=8
行业舆情	首页 > 行业资讯 > 热点观察	http://www.csia.net.cn/Article/ShowClass.asp?ClassID=9
行业舆情	首页 > 行业资讯 > 产品与技术	http://www.csia.net.cn/Article/ShowClass.asp?ClassID=10''')
    # print(getTimeStamp('2022-02-21T13:48:13+08:00'))
    # print(result)
    # print(date2time(date_str='2022-04-19'))

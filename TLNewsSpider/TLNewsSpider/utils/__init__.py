import re
import time
import json
import datetime
import hashlib
import scrapy
from ..settings import PAGE_LIMIT, TIME_LIMIT

def hash_md5(text):
    md5 = hashlib.md5()
    if isinstance(text, str):
        text = text.encode()
    md5.update(text)
    return md5.hexdigest()

class IgNoreException(BaseException):

    def __str__(self):
        print("忽略非标准数据")

def date(timestamp=None, format='%Y-%m-%d %H:%M:%S'):
    '''
    时间戳格式化转换日期
    @params
            timestamp ：时间戳，如果为空则显示当前时间
            format : 时间格式
        @return
            返回格式化的时间，默认为 2014-07-30 09:50 这样的形式
        '''
    if timestamp is None:
        timestamp = int(time.time())
    if not isinstance(timestamp, int):
        timestamp = int(timestamp)
    if len(str(timestamp)) >= 10:
        timestamp = int(str(timestamp)[:10])
    d = datetime.datetime.fromtimestamp(timestamp)
    return d.strftime(format)

def date2time(date_str=None,min_str=None,time_str=None):
    if date_str:
        time_struct = time.strptime(date_str, "%Y-%m-%d")
    if time_str:
        time_struct = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    if min_str:
        time_struct = time.strptime(min_str, "%Y-%m-%d %H:%M")
    time_stamp = time.mktime(time_struct)
    return time_stamp

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

def over_page(page_url, response, page_num=0, page_time=None,callback=None,formdata=None,headers=None,body=None,dont_filter=None):
    '''
    限制最多翻页数 无需限制时在
    '''
    if TIME_LIMIT> 0 and page_time:
        page_str= page_time - int(time.time() - TIME_LIMIT * 86400)
    else:
        page_str= 1
    if page_str<0:
        print("PAGE_JUDGE: ", page_url, page_time)
        raise Exception('超出限制时间')
    else:
        if PAGE_LIMIT > 0 and page_num >= PAGE_LIMIT:
            print("PAGE LIMIT: ", page_url, page_num)
            raise Exception('超出翻页范围')
        if formdata :
            yield scrapy.FormRequest(url=page_url, callback=callback, meta=response.meta, formdata=formdata,headers=headers,dont_filter=dont_filter)
        elif body:
            yield scrapy.Request(url=page_url, callback=callback, meta=response.meta, body=body,headers=headers,method='POST',dont_filter=dont_filter)
        else:
            yield scrapy.Request(url=page_url, callback=callback, meta=response.meta,headers=headers,dont_filter=dont_filter)
            

if __name__ == '__main__':
    pass
    print(hash_md5('你是一个好人'))
    
    
    

#     result = trans_str('''企业舆情	财经 > 证券 > 上市公司	https://finance.ifeng.com/shanklist/1-62-83-/
# 行业舆情	首页 > 旅游	https://travel.ifeng.com/
# 企业舆情	首页 > 财经>股票 > 新股	https://finance.ifeng.com/ipo/
# 企业舆情	首页 > 股票 > 上市公司	https://finance.ifeng.com/shanklist/1-62-83-
# 企业舆情	首页 > 港股 > 公司动态	https://finance.ifeng.com/shanklist/1-69-35250-''')

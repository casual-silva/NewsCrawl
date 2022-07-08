# -*- coding: utf-8 -*-


import sys
sys.path.append('..\..')
sys.path.append('../..')

import json
import time
from TLNewsSpider.package.database.model_archemy import *
from TLNewsSpider.package.Kafaka.config import PRODUCER_CONFIG
from TLNewsSpider.package.Kafaka import kafaka_ctl
session = DBSession()

kafaka_ctl.init_producer(**PRODUCER_CONFIG)

# 去除
def remove_unicode(s):
    return ''.join(x for x in s if x.isprintable())

classify_amp = {
    '地区舆情': 'DQ',
    '行业舆情': 'HY',
    '企业舆情': 'CO',
    '行业研报': 'IR',
    '宏观舆情': 'MO',
    '企业公告': 'CN'
}

def main(limit=1):
    '''
    limit: 单次查询数量
    '''
    for row in session.query(CeNew).filter(CeNew.status == 0).limit(limit):
        content_object = session.query(CeNewsContent).filter(row.uuid == CeNewsContent.uuid).first()
        row_classify = row.classification
        classify = classify_amp.get(row_classify, '无')
        content__text = remove_unicode(content_object.content_text)
        params = {
            "newsId" : row.uuid,  # 舆情唯一标识uuid
            "title": row.title,  # 标题
            "text" :content__text,  # 正文
            "classify": classify,
            "companyName":'',          # 公司名称
            "industryName":'',
            "datasourceUrl":row.source_url,
            "date" :row.publish_date,  # 舆情发布时间

        }
        # 任意一个为空值则过滤
        if not all([params["title"], params["text"], params["date"]]):
            # 无效数据
            row.status = 2
        else:
            try:
                kafaka_ctl.send_data('resource_topic', value=params, partition=0)
                row.status = 1
            except Exception as e:
                row.status = 2
        session.commit()
        print(f'数据提交成功 >> status: {row.status} uuid:{row.uuid} title: {row.title}')



if __name__ == '__main__':
    while True:
        limit = 20
        main(limit)
        time.sleep(10)


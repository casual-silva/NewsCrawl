FROM python:3.7.1
MAINTAINER Silva for_billy@163.com

WORKDIR /home/spider_workplace/TLNewsCrawl

COPY ./requirements.txt ./
RUN apt-get update && apt-get install -y vim
RUN rm -f /etc/localtime && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo Asia/Shanghai > /etc/timezone && export TZ=Asia/Shanghai && export SCHEDULER_TIMEZONE=Asia/Shanghai\
    && python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple\
    && pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple\
    && pip install --upgrade pymysql  -i https://pypi.tuna.tsinghua.edu.cn/simple
    
CMD ["pip", "list"]
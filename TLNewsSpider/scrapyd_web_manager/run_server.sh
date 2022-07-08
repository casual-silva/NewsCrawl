#!/bin/bash

# scrapyd-web 启动，停止，重启

notes='
启动服务：bash run_server.sh start
停止服务：bash run_server.sh stop
重启服务：bash run_server.sh restart
实时日志：bash run_server.sh tail
'

action=$1

function star_server(){
	nohup scrapydweb > scrapydweb.log & echo $! > scrapydweb.pid
	tail -f scrapydweb.log
}

function stop_server(){
	echo "杀死进程：" `cat scrapydweb.pid`
	kill -9 `cat scrapydweb.pid`
}

function restart_server(){
	stop_server
	sleep 2
	star_server
}

function tail_server(){
	tail -200f scrapydweb.log
}

if [ -z "$action" ];
then
    echo "${notes}"
    echo "Error: action param is not null"
    
elif [ $action = "-h"  ] || [ $action = "--help"  ] || [ $action = "h"  ]
then
	echo "${notes}"
	echo "确保启用了conda环境"
elif [ "$action" = "start"  ]
then
	star_server
elif [ "$action" = "stop"  ]
then
	stop_server
elif [ "$action" = "restart"  ]
then
	restart_server
elif [ "$action" = "tail"  ]
then
	tail_server
else
     echo "Error: param error"
fi
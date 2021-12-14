#!/bin/bash

while true; do
# 打印跟在本文件后面的命令行参数 本文件在run.bash中被调用
    echo "starting: $@"
    eval $@
    sleep 60
done

#!/bin/bash

# export DISPLAY=:0

# Xvfb $DISPLAY -screen 0 1920x1080x24+32 &
# watchdog.bash文件用于监测worker运行状态 每分钟检测一次 输出“python /src/run_worker.py lean_and_mean python /src/run.py ”
# python /src/run_worker.py lean_and_mean 后面跟着的&表示python /src/run_worker.py lean_and_mean会转到后台运行
# $@表示脚本的参数值 也就是说在调用run.bash脚本的时候 该脚本可以引用命令行后面全部的参数，参数之间使用空格分隔
/src/worker/watchdog.bash python /src/run_worker.py lean_and_mean &

python /src/run.py $@

#!/usr/local/bin/python3
# encoding=utf-8
import datetime
import os
import threading


def execCmd(cmd):
    try:
        print("命令%s开始运行%s" % (cmd, datetime.datetime.now() ))
        os.system(cmd)
        print("命令%s结束运行%s" % (cmd, datetime.datetime.now()))
    except Exception as e:       #异常处理,此处声明.没有刻意计划异常处理,(只确保我执行的linux命令键入正确即可),[所以有报错也不会打印如下异常])
        print('命令%s\t 运行失败,失败原因\r\n%s' % (cmd,e))


if __name__ == '__main__':
    # 需要执行的命令列表
    cmds = [ 'conda env list','python --version']   #为突出效果,此处的shell脚本,我将前面的休眠3s.会发现后面脚本先行执行完毕.多线程成功
    # 线程池
    threads = []

    print("程序开始运行%s" % datetime.datetime.now())

    for cmd in cmds:    #将需要执行的linux命令列表 放入for循环
        th = threading.Thread(target=execCmd, args=(cmd,))  #调用函数,引入线程参数
        th.start()          #开始执行
        threads.append(th)

    # 等待线程运行完毕
    for th in threads:
        th.join()       #循环 join()方法可以让主线程等待所有的线程都执行完毕

    print("程序结束运行%s" % datetime.datetime.now())
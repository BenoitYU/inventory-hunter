# import subprocess

# #conda env list
# a= subprocess.run("python ./src/ThreadTest1.py", stdout=subprocess.PIPE)    # 捕获输出
# print(a.stdout.decode("GBK"))

# b= subprocess.run("python ./src/ThreadTest2.py", stdout=subprocess.PIPE)    # 捕获输出
# print(b.stdout.decode("GBK"))

import multiprocessing
import time, datetime
import os


def function1():
    for i in range(5):
        time.sleep(2)
        print(f'this is in thread 1, the cycle number is {i} \n')

def function2():
    for i in range(5):
        time.sleep(2)
        print(f'this is in thread 2, the cycle number is {i} \n')

def execCmd(cmd):
    try:
        print("命令%s开始运行%s" % (cmd, datetime.datetime.now() ))
        os.system(cmd)
        print("命令%s结束运行%s" % (cmd, datetime.datetime.now()))

    #异常处理,此处声明.没有刻意计划异常处理,(只确保我执行的linux命令键入正确即可),[所以有报错也不会打印如下异常])
    except Exception as e :       
        print('命令%s\t 运行失败,失败原因\r\n%s' % (cmd,e))


def main():
    processes = []

    process1 = multiprocessing.Process(target=execCmd,args=('python ./multiProcess/ThreadTest1.py',))
    processes.append(process1)
    process1.start()

    process2 = multiprocessing.Process(target=execCmd,args=('python ./multiProcess/ThreadTest2.py',))
    processes.append(process1)
    process2.start()

    #循环 join()方法可以让主线程等待所有的线程都执行完毕 若缺失则主线程直接自己结束而不等待分线程
    for proc in processes:
            proc.join()

if __name__ == '__main__':
    main()
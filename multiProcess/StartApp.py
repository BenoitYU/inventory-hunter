#注意 python运行的根目录实在INVENTORY-HUNTER 即便是文件都在MultiProcess里面 调用的时候也需要输入从根目录出发的相对地址
import multiprocessing
import time, datetime
import os

def execCmd(cmd):
    try:
        print("命令%s开始运行%s" % (cmd, datetime.datetime.now() ))
        os.system(cmd)
        print("命令%s结束运行%s" % (cmd, datetime.datetime.now()))

    except Exception as e :       
        print('命令%s\t 运行失败,失败原因\r\n%s' % (cmd,e))

def main():
    processes = []
    cmdCommande1='python ./src/run_worker.py lean_and_mean'
    #cmdCommande1='python --version'
    cmdCommande2='python ./src/run.py -a email -c ./config/amazon_rtx_3080.yaml -q ./config/alerters.yaml -l ./log.txt'
 
    process1 = multiprocessing.Process(target=execCmd,args=(cmdCommande1,))
    processes.append(process1)
    process1.start()

    process2 = multiprocessing.Process(target=execCmd,args=(cmdCommande2,))
    processes.append(process2)
    process2.start()

    #循环 join()方法可以让主线程等待所有的线程都执行完毕 若缺失则主线程直接自己结束而不等待分线程
    for proc in processes:
            proc.join()

if __name__ == '__main__':
    main()
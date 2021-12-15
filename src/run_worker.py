import argparse
import importlib
import logging


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('worker')
    return parser.parse_args()


def main():
    #设置log格式
    args = parse_args()
    log_format = '{{levelname:.1s}}{{asctime}} [{args.worker}] {{message}}'
    logging.basicConfig(level=logging.ERROR, format=log_format, style='{')
    
    logger = logging.getLogger()
    #在项目根目录创建模块log文件
    handler = logging.FileHandler(f'./{args.worker}.txt')
    handler.setFormatter(logging.Formatter(log_format, style='{'))
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    #import_module只是简单地执行和import相同的步骤，但是返回生成的模块对象。你只需要将其存储在一个变量，然后像正常的模块一样使用
    #主要是解决‘你想导入一个模块，但是模块的名字在字符串里。你想对字符串调用导入命令’ 也就是包名字是变量的问题 动态导入
    pkg = importlib.import_module(f'worker.{args.worker}')
    pkg.run()


if __name__ == '__main__':
    main()

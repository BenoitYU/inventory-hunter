import logging
# 注意可能会遇到已安装ppyaml但还是无法找到yaml包的问题 解决方法是直接在vscode中的终端执行pip install pyyaml 即可
import yaml

from abc import ABC, abstractmethod
from collections.abc import Callable
#简单来说，包就是文件夹，但该文件夹下必须存在 __init__.py 文件, 该文件的内容可以为空。__init__.py 用于标识当前文件夹是一个包。
#Python模块(Module)，是一个 Python 文件，以 .py 结尾，包含了 Python 对象定义和Python语句。
# 包括：普通方法、静态方法和类方法，三种方法在内存中都归属于类，区别在于调用方式不同

# 普通方法：由对象调用；至少一个self参数；执行普通方法时，自动将调用该方法的对象赋值给self；
# 类方法：由类调用； 至少一个cls参数；执行类方法时，自动将调用该方法的类复制给cls；
# 静态方法：由类调用；无默认参数；
# 三者相同点：对于所有的方法而言，均属于类（非对象）中，所以，在内存中也只保存一份
# 三者不同点：方法调用者不同、调用方法时自动传入的参数不同

#@property：方法伪装属性，方法返回值及属性值，被装饰方法不能有参数，必须实例化后调用，类不能调用
#@staticmethod：静态方法，可以通过实例对象和类对象调用，被装饰函数可无参数，被装饰函数内部通过类名.属性引用类属性或类方法，不能引用实例属性
#@abstractmethod用于程序接口的控制，正如上面的特性，含有@abstractmethod修饰的父类不能实例化，但是继承的子类必须实现@abstractmethod装饰的方法
#@classmethod修饰符对应的函数不需要实例化，不需要 self 参数，但第一个参数需要是表示自身类的 cls 参数，可以来调用类的属性，类的方法，实例化对象等 但是注意不能调用实例属性
#格式化字符串用法https://blog.csdn.net/sunxb10/article/details/81036693
#Alerter继承多个类 包括Callable类 从而使得Alerter类可以在函数之间传递

class Alerter(ABC, Callable):
    #__init__()函数的意义等同于类的构造器（同理，__del__()等同于类的析构函数）。因此，__init__()方法的作用是初始化一个类的实例
    #Alerter.__init__(**kwargs)就等于Alerter(**kwargs)
    def __init__(self, **kwargs):
        pretty_kwargs = ' '.join([f'{k}={v}' for k, v in kwargs.items()])
        logging.info(f'{self.get_alerter_type()} alerter initialized with kwargs: {pretty_kwargs}')

    @classmethod
    @abstractmethod
    def from_args(cls, args):
        pass

    @classmethod
    @abstractmethod
    def from_config(cls, config):
        pass

    @staticmethod
    @abstractmethod
    def get_alerter_type():
        pass

class AlertEngine:
    def __init__(self, alerters):
        self.alerters = alerters
        #如果alerters是空值的话 弹出异常
        if not self.alerters:
            raise Exception('no alerters loaded')

    def __call__(self, **kwargs):
        for alerter in self.alerters:
            try:
                alerter(**kwargs)
            except Exception:
                logging.exception(f'{alerter.get_alerter_type()} alerter failed to alert')

#根据传进来的是具体参数还是文本来分情况
class AlerterFactory:
    registry = dict()

    @classmethod
    def create(cls, args):
        if args.alerter_config is None:
            return cls.create_from_args(args)
        else:
            return cls.create_from_config(args.alerter_config)

    @classmethod
    def create_from_args(cls, args):
        alerter = cls.get_alerter(args.alerter_type)
        return AlertEngine([alerter.from_args(args)])

    @classmethod
    def create_from_config(cls, config):
        data = yaml.safe_load(config)
        alerters = []
        for alerter_type, alerter_config in data['alerters'].items():
            alerter = cls.get_alerter(alerter_type)
            alerters.append(alerter.from_config(alerter_config))
        return AlertEngine(alerters)

    @classmethod
    def get_alerter(cls, alerter_type):
        if alerter_type not in cls.registry:
            raise Exception(f'the "{alerter_type}" alerter type does not exist in the registry')
        return cls.registry[alerter_type]

    @classmethod
    def register(cls, alerter):
        alerter_type = alerter.get_alerter_type()
        logging.debug(f'registering alerter type: {alerter_type}')
        cls.registry[alerter_type] = alerter
        return alerter

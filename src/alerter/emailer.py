import logging
import smtplib

from email.message import EmailMessage
from email.utils import formatdate

from alerter.common import Alerter, AlerterFactory


@AlerterFactory.register
#EmailAlerter继承自Alerter
class EmailAlerter(Alerter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #strip() 方法用于移除字符串头尾指定的字符（默认为空格或换行符）或字符序列
        self.sender = kwargs.get('sender').strip()
        recipients = kwargs.get('recipients')
        if not isinstance(recipients, list):
            recipients = [recipients]
        self.recipients = [r.strip() for r in recipients]
        self.relay = kwargs.get('relay')
        self.password = kwargs.get('password', None)

    @classmethod
    def from_args(cls, args):
        sender = args.email[0]
        recipients = args.email
        relay = args.relay
        return cls(sender=sender, recipients=recipients, relay=relay)

    @classmethod
    def from_config(cls, config):
        sender = config['sender']
        recipients = config['recipients']
        relay = config['relay']
        password = config.get('password', None)
        return cls(sender=sender, recipients=recipients, relay=relay, password=password)

    @staticmethod
    def get_alerter_type():
        return 'email'
    # 为了将一个类实例当做函数调用，我们需要在类中实现__call__()方法。也就是我们要在类中实现如下方法：def __call__(self, *args)。这个方法接受一定数量的变量作为输入。
    # 假设x是X类的一个实例。那么调用x.__call__(1,2)等同于调用x(1,2)。这个实例本身在这里相当于一个函数一样被调用
    def __call__(self, **kwargs):
        msg = EmailMessage()

        set_subject = kwargs.get("subject").strip()
        set_content = kwargs.get("content")

        msg.add_header("Date", formatdate())
        msg.set_content(set_content)
        if set_subject:
            msg["Subject"] = set_subject
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)
        with smtplib.SMTP(self.relay) as s:
            logging.debug(f"sending email: subject: {set_subject}")
            if self.password:
                s.login(self.sender, self.password)
            s.send_message(msg)

import datetime
import locale
import logging
import re

# required for price parsing logic
locale.setlocale(locale.LC_ALL, '')

from abc import ABC, abstractmethod
from bs4 import BeautifulSoup

#ABC，Abstract Base Class（抽象基类），主要定义了基本类和最基本的抽象方法，可以为子类定义共有的API，不需要具体实现。
class ScrapeResult(ABC):
    def __init__(self, logger, r, last_result):
        self.alert_subject = None
        self.alert_content = None
        self.captcha = False
        self.forbidden = True if r.status_code == 403 else False
        self.logger = logger
        self.previously_in_stock = bool(last_result)
        self.price = None
        self.price_pattern = re.compile('[0-9,.]+')
        self.price_comma_pattern = re.compile('^.*\\,\\d{2}$')
        self.last_price = last_result.price if last_result is not None else None
        self.soup = BeautifulSoup(r.text, 'lxml')
        self.content = self.soup.body.text.lower()  # lower for case-insensitive searches
        self.url = r.url
        #如果返回的结果中status_code的值不是 403 则调用parse函数解析 从而更新alert_subject和alert_content的值
        if not self.forbidden:
            self.parse()
    #此处ScrapeResult.__bool__可以直接省略为ScrapeResult 就是根据content变量中有无内容来返回bool的值
    def __bool__(self):
        return bool(self.alert_content)
    #判断phrase似乎否存在self.content中 self.content即为网页的soup.body.text.lower()形式内容
    def has_phrase(self, phrase):
        return phrase in self.content
    #提取价格并转化为Float格式然后赋值给self.price
    #如果有价格且成功从网页中提取出来并转换为float 则self.price不为空 其余情况全部为Non
    def set_price(self, tag):
        #如果tage的内容为空 则直接退出 self.price保持Non
        if not tag:
            return

        price_str = tag if isinstance(tag, str) else tag.text.strip()
        if not price_str:
            return

        re_match = self.price_pattern.search(price_str)
        if not re_match:
            self.logger.warning(f'unable to find price in string: "{price_str}"')
            return

        re_match_str = re_match.group()
        if self.price_comma_pattern.match(re_match_str):
            comma_index = re_match_str.rfind(',')
            if comma_index != -1:
                re_match_str = f'{re_match_str[:comma_index].replace(".", ",")}.{re_match_str[comma_index+1:]}'

        try:
            self.price = locale.atof(re_match_str)
        except Exception as e:
            self.logger.warning(f'unable to convert "{price_str}" to float... caught exception: {e}')

        return price_str
    #后续针对不同的网站 进行不同的内容解析函数定义
    @abstractmethod
    def parse(self):
        pass

#此处是针对一般的网站的解析函数的实现 注意 在这个模式中并灭有对价格进行提取 所以其默认为Non
class GenericScrapeResult(ScrapeResult):
    def parse(self):
        # not perfect but usually good enough
        #通过判断'add to cart'或者'add to basket'是否可以从网页内容中找到来判定商品是否avaiable
        if self.has_phrase('add to cart') or self.has_phrase('add to basket'):
            self.alert_subject = 'In Stock'
            self.alert_content = self.url

#监测爬虫的表现水平
class ScraperStats:
    def __init__(self):
        self.reset()

    def get_failure_rate(self):
        return 100.0 * self.num_failed / self.get_number_of_scrapes()

    def get_success_rate(self):
        return 100.0 * self.num_successful / self.get_number_of_scrapes()

    def get_number_of_scrapes(self):
        total = self.num_successful + self.num_failed
        return total if total else 1  # to prevent divide by zero

    def reset(self):
        self.num_successful = 0
        self.num_failed = 0
        self.since_time = datetime.datetime.now()

    def __repr__(self):
        now = datetime.datetime.now()
        diff = now - self.since_time
        success_rate = self.get_success_rate()
        return (
            f'{self.num_successful} successful scrapes '
            f'in the last {diff.total_seconds():.0f} seconds '
            f'({success_rate:.0f}% success rate)'
        )

#用于爬取网站的类
class Scraper(ABC):
    #注意此处的url是后面定义的URL类的实例 不是单纯的链接
    def __init__(self, drivers, url):
        self.driver = getattr(drivers, self.get_driver_type())
        self.filename = drivers.data_dir / f'{url.nickname}.html'
        self.logger = logging.getLogger(url.nickname)
        self.stats = ScraperStats()
        self.url = url
        self.last_result = None
        self.logger.info(f'scraper initialized for {self.url}')

    @staticmethod
    @abstractmethod
    def get_domain():
        pass

    @staticmethod
    @abstractmethod
    def get_driver_type():
        pass

    @staticmethod
    @abstractmethod
    def get_result_type():
        pass

    def scrape(self):
        #调用scrape_impl进行网页爬取
        r = self.scrape_impl()
        #如果成功获取网页内容 则算作成功爬取一次 否则记作失败
        if r is not None:
            self.stats.num_successful += 1
        else:
            self.stats.num_failed += 1

        #每五分钟检查一下爬取的performance
        if datetime.datetime.now() - self.stats.since_time > datetime.timedelta(minutes=5):
            log_level = logging.WARN if self.stats.get_failure_rate() > 0 else logging.INFO
            self.logger.log(log_level, self.stats)
            self.stats.reset()

        return r
    #爬取网页内容 并根据result_type 创建ScrapeResult实例 可以是GenericScrapeResult 也可以是具体网站的结果类型 如AmazonScrapeResult
    def scrape_impl(self):
        try:
            self.logger.debug('starting new scrape')
            #打开网页链接
            r = self.driver.get(self.url)
            if self.get_driver_type() != 'puppeteer':
                with self.filename.open('w') as f:
                    f.write(r.text)
            result_type = self.get_result_type()
            #根据返回的类型创建结果实例
            this_result = result_type(self.logger, r, self.last_result)
            self.last_result = this_result
            return this_result

        except Exception as e:
            self.logger.error(f'caught exception during request: {e}')
            self.stats.num_failed += 1


class GenericScraper(Scraper):
    @staticmethod
    def get_domain():
        return 'generic'

    @staticmethod
    def get_driver_type():
        return 'requests'

    @staticmethod
    def get_result_type():
        return GenericScrapeResult

#该类主要是根据url.netloc来确定网站的爬取方式应该是通用还是特殊 通用就用genericscrap 特殊的话 则采用指定scrape类型
class ScraperFactory:
    registry = dict()

    @classmethod
    def create(cls, drivers, url):
        for domain, scraper_type in cls.registry.items():
            if domain in url.netloc:
                return scraper_type(drivers, url)
        logging.warning(f'warning: using generic scraper for url: {url}')
        return GenericScraper(drivers, url)

    @classmethod
    def register(cls, scraper_type):
        domain = scraper_type.get_domain()
        logging.debug(f'registering custom scraper for domain: {domain}')
        cls.registry[domain] = scraper_type
        return scraper_type

import random
import sched
import sys


random.seed()

# scrapers 表示的是对应的config文件中的所有的链接爬取 每一个爬取任务就是一个scraper类实例 然后这个实例会被加入到scheduler中一直循环调用 
# 需要注意的是 一个config文件对应着一件商品 一个上平对应着多个网站 每一个网站对应着一个爬取任务 每个爬取任务会被无休止循环执行
class Engine:
    def __init__(self, alerters, config, scrapers):
        self.alerters = alerters
        self.refresh_interval = config.refresh_interval
        self.max_price = config.max_price
        self.scheduler = sched.scheduler()
        #每一个s都是Scraper类的一个实例 对应着对一个网站的爬取任务
        for s in scrapers:
            self.schedule(s)

    def run(self):
        self.scheduler.run(blocking=True)
    #该函数把一个scraper的实例s的爬取任务加入时间表
    def schedule(self, s):
        time_delta = self.refresh_interval

        # semi-random intervals throw off some web scraping defenses
        time_delta *= random.randint(100, 120) / 100.0

        #根据scheduler内部的任务数量分情况确定任务执行的时间
        if self.scheduler.queue:
            t = self.scheduler.queue[-1].time + time_delta
            #表示在t时间的时候执行 Engine.tick(self, s) 这个调用 其中(self, s) 是Engine.tick的输入参数
            self.scheduler.enterabs(t, 1, Engine.tick, (self, s))
        else:
            self.scheduler.enter(time_delta, 1, Engine.tick, (self, s))
    # 每执行一次任务 然后添加下个任务
    def tick(self, s):
        #返回的result是ScrapeResult类的实例
        result = s.scrape()

        if result is None:
            s.logger.error('scrape failed')
        else:
            self.process_scrape_result(s, result)
        #结束对网站的一次爬取后 把新的爬取任务加入时间轴 等待下一次爬取 所以一旦开启engine后 不会自己停止
        return self.schedule(s)

    def process_scrape_result(self, s, result):
        #先查看服务器返回结果是否无效
        if result.captcha:
            s.logger.warning('access denied, got a CAPTCHA')
            return
        elif result.forbidden:
            s.logger.warning('access denied, got HTTP status code 403 (forbidden)')
            return
        #如果result.alert_content不为空 则说明有存货
        currently_in_stock = bool(result)
        previously_in_stock = result.previously_in_stock
        current_price = result.price
        last_price = result.last_price

        if currently_in_stock and previously_in_stock:
            #注意 此处的逻辑是 因为找到了‘加入购物车’选项 所以一定有存货 所以要是价格还是Non的话 只
            #能说没有正确提取出来价格而不是价格不存在 所以才有了第一个if的判断逻辑
            # if no pricing is available, we'll assume the price hasn't changed
            if current_price is None or last_price is None:
                s.logger.info('still in stock')
            #如果正常提取出来而且相同的话
            # is the current price the same as the last price? (most likely yes)
            elif current_price == last_price:
                s.logger.info('still in stock at the same price')

            # has the price gone down?
            elif current_price < last_price:

                if self.max_price is None or current_price <= self.max_price:
                    self.send_alert(s, result, f'now in stock at {current_price}!')
                else:
                    s.logger.info(f'now in stock at {current_price}... still too expensive')

            else:
                s.logger.info(f'now in stock at {current_price}... more expensive than before :(')

        elif currently_in_stock and not previously_in_stock:

            # if no pricing is available, we'll assume the price is low enough
            #此处没有价格可以理解为价格没有从网页正常提取出来
            if current_price is None:
                self.send_alert(s, result, 'now in stock!')

            # is the current price low enough?
            elif self.max_price is None or current_price <= self.max_price:
                self.send_alert(s, result, f'now in stock at {current_price}!')

            else:
                s.logger.info(f'now in stock at {current_price}... too expensive')
        #如果碰到了需要验证的情况 需要此处补充一下验证的检测机制
        elif not currently_in_stock and result.has_phrase('are you a human'):
            
            s.logger.error('got "are you a human" prompt')
            self.alerters(subject='Something went wrong',
                          content=f'You need to answer this CAPTCHA and restart this script: {result.url}')
            sys.exit(1)

        else:
            s.logger.info('not in stock')

    def send_alert(self, s, result, reason):
        s.logger.info(reason)
        #注意 此处是如何确定选用何种方法发送alerts的
        self.alerters(subject=result.alert_subject, content=result.alert_content)


def hunt(alerters, config, scrapers):
    engine = Engine(alerters, config, scrapers)
    engine.run()

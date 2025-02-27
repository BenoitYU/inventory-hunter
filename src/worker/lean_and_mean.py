import logging
# aiohttp是一个异步的 HTTP 客户端\服务端框架，基于 asyncio 的异步模块。可用于实现异步爬虫，更快于 requests 的同步爬虫
# 该模块用了aiohttp模块 创建了一个服务器+客户端 使用谷歌的protobuf处理字节流 优点是更快速
import aiohttp
import urllib.parse

from worker.registry import Endpoint, EndpointRegistry
from worker.server import Server


@EndpointRegistry.register
class LeanAndMeanServer(Server):
    _endpoint = Endpoint(__file__, '127.0.0.1', 3080)

    def __init__(self):
        super().__init__(self._endpoint)
        self.headers = {
            'accept': 'text/html',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'dnt': '1',
            'pragma': 'no-cache',
            'referer': 'https://google.com',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36',
        }

    async def handle_request(self, request, writer):
        self.headers['authority'] = urllib.parse.urlparse(request.url).netloc
        async with aiohttp.ClientSession(headers=self.headers) as session:
            timeout = request.timeout if request.timeout else 30
            async with session.get(request.url, timeout=timeout) as r:
                data = await r.text()
                # 将网页信息序列化存入writer
                writer.write(self.encode_response(
                    response_id=request.id,
                    data=data,
                    status_code=r.status,
                ))
                writer.write_eof()
                logging.info(f'sent response: id: {request.id}, status_code: {r.status}, data: <{len(data)} bytes>')


def run():
    server = LeanAndMeanServer()
    server.run()

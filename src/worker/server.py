import asyncio
import logging

from abc import ABC, abstractmethod

import worker.worker_pb2 as spec


class Server(ABC):
    def __init__(self, endpoint):
        self._response = spec.Response()

    def decode_request(self, data) -> spec.Request:
        request = spec.Request()
        request.ParseFromString(data)
        return request

    def encode_response(self, response_id: int, data: str, status_code: int) -> str:
        self._response.Clear()
        self._response.id = response_id
        self._response.data = data
        self._response.status_code = status_code
        return self._response.SerializeToString()

    #此处的输入reader writer 应该是在建立连接的时候附带的参数 详情查看client.get_impl函数
    #而且是client的writer=>服务器的reader=>服务器的writer=>client的reader这样一个流程
    async def handle(self, reader, writer):
        try:
            #先对序列信息进行解码
            request = self.decode_request(await reader.read())
            logging.info(f'received request: id: {request.id}, url: {request.url}, timeout: {request.timeout}')
            #等待handle_request获取网页信息然后返回内容
            await self.handle_request(request, writer)
        except Exception as e:
            logging.error(f'something went wrong during request: {e}')

        writer.close()
        await writer.wait_closed()

    @abstractmethod
    async def handle_request(self, request, writer):
        pass

    async def run_impl(self):
        #启动服务器 服务器的回应是handle函数
        server = await asyncio.start_server(self.handle, self._endpoint.addr, self._endpoint.port)
        async with server:
            await server.serve_forever()

    def run(self):
        asyncio.run(self.run_impl())

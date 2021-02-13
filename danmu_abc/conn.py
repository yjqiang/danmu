import json
import asyncio
from typing import Optional, Any
from urllib.parse import urlparse
from abc import ABC, abstractmethod

from aiohttp import ClientSession, WSMsgType, ClientError


class Conn(ABC):
    __slots__ = ('_url', '_receive_timeout',)

    # receive_timeout 推荐为 heartbeat 间隔加 10s 或 5s
    @abstractmethod
    def __init__(self, url: str, receive_timeout: Optional[float] = None):
        self._url = url
        self._receive_timeout = receive_timeout

    @abstractmethod
    async def open(self) -> bool:
        return False

    @abstractmethod
    async def close(self) -> bool:
        return True
        
    # 用于永久 close 之后一些数据清理等
    @abstractmethod
    async def clean(self) -> None:
        pass

    @abstractmethod
    async def send_bytes(self, bytes_data: bytes) -> bool:
        return True

    @abstractmethod
    async def read_bytes(self) -> Optional[bytes]:
        return None

    @abstractmethod
    async def read_json(self) -> Any:
        return None

    # 类似于 https://docs.python.org/3/library/asyncio-stream.html#asyncio.StreamReader.readexactly
    # Read exactly n bytes.
    @abstractmethod
    async def read_exactly_bytes(self, n: int) -> Optional[bytes]:
        return None

    # 类似于 https://docs.python.org/3/library/asyncio-stream.html#asyncio.StreamReader.readexactly
    # Read exactly n bytes.
    @abstractmethod
    async def read_exactly_json(self, n: int) -> Any:
        return None
        
        
class TcpConn(Conn):
    __slots__ = ('_host', '_port', '_reader', '_writer')

    # url 格式 tcp://hostname:port
    def __init__(self, url: str, receive_timeout: Optional[float] = None):
        super().__init__(url, receive_timeout)
        result = urlparse(url)
        if result.scheme != 'tcp':
            raise TypeError(f'url scheme must be tcp ({result.scheme})')

        self._host = result.hostname
        self._port = result.port
        self._reader = None
        self._writer = None
        
    async def open(self) -> bool:
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), timeout=3)
        except (OSError, asyncio.TimeoutError):
            return False
        return True
        
    async def close(self) -> bool:
        if self._writer is not None:
            self._writer.close()
            # py3.7 才有（妈的你们真的磨叽）
            # await self._writer.wait_closed()
        return True
    
    async def clean(self) -> None:
        pass
        
    async def send_bytes(self, bytes_data: bytes) -> bool:
        try:
            self._writer.write(bytes_data)
            await self._writer.drain()
        except OSError:
            return False
        except asyncio.CancelledError:
            # print('asyncio.CancelledError', 'send_bytes')
            return False
        return True

    async def read_bytes(self) -> Optional[bytes]:
        # 不支持的原因是，tcp 流式传输，自己拼装过于复杂
        raise NotImplementedError("Sorry, but I don't think we need this in TCP.")

    async def read_json(self) -> Any:
        # 不支持的原因是，tcp 流式传输，自己拼装过于复杂
        raise NotImplementedError("Sorry, but I don't think we need this in TCP.")
        
    async def read_exactly_bytes(self, n: int) -> Optional[bytes]:
        if n <= 0:
            return None
        try:
            bytes_data = await asyncio.wait_for(
                self._reader.readexactly(n), timeout=self._receive_timeout)
        except (OSError, asyncio.TimeoutError, asyncio.IncompleteReadError):
            return None
        except asyncio.CancelledError:
            # print('asyncio.CancelledError', 'read_bytes')
            return None
        return bytes_data
        
    async def read_exactly_json(self, n: int) -> Any:
        data = await self.read_exactly_bytes(n)
        if not data:
            return None
        return json.loads(data.decode('utf8'))
                

class WsConn(Conn):
    __slots__ = ('_is_sharing_session', '_session', '_ws_receive_timeout', '_ws_heartbeat', '_ws')

    # url 格式 ws://hostname:port/… 或者 wss://hostname:port/…
    def __init__(
            self, url: str,
            receive_timeout: Optional[float] = None,
            session: Optional[ClientSession] = None,
            ws_receive_timeout: Optional[float] = None,  # 自动 ping pong 时候用的
            ws_heartbeat: Optional[float] = None):  # 自动 ping pong 时候用的
        super().__init__(url, receive_timeout)
        result = urlparse(url)
        if result.scheme != 'ws' and result.scheme != 'wss':
            raise TypeError(f'url scheme must be websocket ({result.scheme})')
        self._url = url
        
        if session is None:
            self._is_sharing_session = False
            self._session = ClientSession()
        else:
            self._is_sharing_session = True
            self._session = session
        self._ws_receive_timeout = ws_receive_timeout
        self._ws_heartbeat = ws_heartbeat
        self._ws = None

    async def open(self) -> bool:
        try:
            self._ws = await asyncio.wait_for(
                self._session.ws_connect(
                    self._url,
                    receive_timeout=self._ws_receive_timeout,
                    heartbeat=self._ws_heartbeat), timeout=3)
        except (ClientError, asyncio.TimeoutError):
            return False
        return True
        
    async def close(self) -> bool:
        if self._ws is not None:
            await self._ws.close()
        return True
        
    async def clean(self) -> None:
        if not self._is_sharing_session:
            await self._session.close()
        
    async def send_bytes(self, bytes_data: bytes) -> bool:
        try:
            await self._ws.send_bytes(bytes_data)
        except ClientError:
            return False
        except asyncio.CancelledError:
            return False
        return True
                
    async def read_bytes(self) -> Optional[bytes]:
        try:
            msg = await asyncio.wait_for(
                self._ws.receive(), timeout=self._receive_timeout)
            if msg.type == WSMsgType.BINARY:
                return msg.data
        except (ClientError, asyncio.TimeoutError):
            return None
        except asyncio.CancelledError:
            # print('asyncio.CancelledError', 'read_bytes')
            return None
        return None

    async def read_json(self) -> Any:
        try:
            msg = await asyncio.wait_for(
                self._ws.receive(), timeout=self._receive_timeout)
            if msg.type == WSMsgType.TEXT:
                return json.loads(msg.data)
            elif msg.type == WSMsgType.BINARY:
                return json.loads(msg.data.decode('utf8'))
        except (ClientError, asyncio.TimeoutError):
            return None
        except asyncio.CancelledError:
            # print('asyncio.CancelledError', 'read_json')
            return None
        return None

    async def read_exactly_bytes(self, n: int) -> Optional[bytes]:
        raise NotImplementedError("Sorry, but I don't think we need this in WebSocket.")

    async def read_exactly_json(self, n: int) -> Any:
        raise NotImplementedError("Sorry, but I don't think we need this in WebSocket.")

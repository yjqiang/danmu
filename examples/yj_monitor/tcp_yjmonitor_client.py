import json

from danmu_abc import TcpConn, Client
from .utils import Header, Pack


class TcpYjMonitorClient(Client):
    __slots__ = ('_key', '_pack_heartbeat')

    def __init__(
            self, key: str, url: str, area_id: int, loop=None):
        heartbeat = 30.0
        conn = TcpConn(
            url=url,
            receive_timeout=heartbeat + 10)
        super().__init__(
            area_id=area_id,
            conn=conn,
            heartbeat=heartbeat,
            loop=loop)
        self._key = key

        self._pack_heartbeat = Pack.pack(str_body='')

    async def _one_hello(self) -> bool:
        dict_enter = {
            'code': 0,
            'type': 'ask',
            'data': {'key': self._key}
            }
        str_enter = json.dumps(dict_enter)
        return await self._conn.send_bytes(Pack.pack(str_body=str_enter))

    async def _one_heartbeat(self) -> bool:
        return await self._conn.send_bytes(self._pack_heartbeat)

    async def _one_read(self) -> bool:
        header = await self._conn.read_bytes(4)
        if header is None:
            return False

        len_body, = Header.unpack(header)

        # 心跳回复
        if not len_body:
            # print('heartbeat')
            return True

        body = await self._conn.read_json(len_body)
        if body is None:
            return False

        json_data = body

        data_type = json_data['type']
        if data_type == 'raffle':
            if not self.handle_danmu(json_data['data']):
                return False
        # 握手确认
        elif data_type == 'entered':
            print(f'确认监控已经连接')
        elif data_type == 'error':
            print(f'发生致命错误{json_data}')
            return False
        return True

    def handle_danmu(self, body):
        print(f'{self._area_id} 号数据连接:', body)
        return True

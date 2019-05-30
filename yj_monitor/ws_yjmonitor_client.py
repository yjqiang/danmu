import json
from typing import Optional

from aiohttp import ClientSession

from client import Client
from conn import WsConn


class WsYjMonitorClient(Client):
    def __init__(
            self, key: str, url: str, area_id: int,
            session: Optional[ClientSession] = None, loop=None):
        heartbeat = 30.0
        conn = WsConn(
            url=url,
            receive_timeout=None,
            session=session,
            ws_heartbeat=heartbeat,
            ws_receive_timeout=heartbeat+10.0
        )
        super().__init__(
            area_id=area_id,
            conn=conn,
            heartbeat=heartbeat,
            loop=loop)
        self._key = key

    @property
    def _hello(self):
        dict_enter = {
            'code': 0,
            'type': 'ask',
            'data': {'key': self._key}
            }
        str_enter = json.dumps(dict_enter)
        bytes_enter = self._encapsulate(str_body=str_enter)
        return bytes_enter

    def _encapsulate(self, str_body):
        body = str_body.encode('utf-8')
        return body

    async def _read_one(self) -> bool:
        body = await self._conn.read_json()
        if body is None:
            return True
        json_data = body

        data_type = json_data['type']
        if data_type == 'raffle':
            if not self.handle_danmu(json_data['data']):
                return True
        # 握手确认
        elif data_type == 'entered':
            print(f'确认监控已经连接')
        elif data_type == 'error':
            print(f'发生致命错误{json_data}')
            return False
        return True

    @staticmethod
    def handle_danmu(body):
        print(body)
        return True

import json
from struct import Struct

from client import Client
from conn import TcpConn


class TcpYjMonitorClient(Client):
    header_struct = Struct('!I')

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

        self._bytes_heartbeat = self._encapsulate(str_body='')
        self._funcs_task.append(self._send_heartbeat)

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
        len_body = len(body)
        header = self.header_struct.pack(len_body)
        return header + body

    async def _read_datas(self):
        while True:
            header = await self._conn.read_bytes(4)
            # 本函数对bytes进行相关操作，不特别声明，均为bytes
            if header is None:
                return

            # 每片data都分为header和body，data和data可能粘连
            # data_l == header_l && next_data_l == next_header_l
            # ||header_l...header_r|body_l...body_r||next_data_l...
            len_body, = self.header_struct.unpack_from(header)
            
            body = await self._conn.read_bytes(len_body)
            if body is None:
                return
            # 心跳回复
            if not body:
                continue
            json_data = json.loads(body.decode('utf-8'))

            data_type = json_data['type']
            if data_type == 'raffle':
                if not self.handle_danmu(json_data['data']):
                    return
            # 握手确认
            elif data_type == 'entered':
                print(f'确认监控已经连接')
            elif data_type == 'error':
                print(f'发生致命错误{json_data}')
                return

    @staticmethod
    def handle_danmu(body):
        print(body)
        return True

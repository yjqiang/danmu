"""本代码参考了
https://github.com/littlecodersh/danmu
https://github.com/dust8/pystt
斗鱼弹幕服务器第三方接入协议v1.6.2.pdf
特此感谢。
"""
import json
from struct import Struct
from typing import Optional

from aiohttp import ClientSession

from client import Client
from conn import WsConn


class WsDanmuClient(Client):
    header_struct = Struct('<2I2H')  # len_data、len_data、send/receive、0

    def __init__(
            self, room_id: int, area_id: int,
            session: Optional[ClientSession] = None, loop=None):
        heartbeat = 45.0
        conn = WsConn(
            url='wss://danmuproxy.douyu.com:8502',
            receive_timeout=heartbeat + 10,
            session=session)
        super().__init__(
            area_id=area_id,
            conn=conn,
            heartbeat=heartbeat,
            loop=loop)
        self._room_id = room_id

        dict_heartbeat = {'type': 'mrkl'}
        self._bytes_heartbeat = self._encapsulate(str_body=self._stt_dumps(dict_heartbeat))
        self._funcs_task.append(self._send_heartbeat)

    @property
    def room_id(self):
        return self._room_id

    @property
    def _hello(self):
        dict_enter = {
            'type': 'loginreq',
            'roomid': str(self._room_id)
        }
        str_enter = self._stt_dumps(dict_enter)
        bytes_enter = self._encapsulate(str_body=str_enter)
        dict_a = {
            'type': 'joingroup',
            'rid': str(self._room_id),
            'gid': str(-9999)
        }
        bytes_enter += self._encapsulate(str_body=self._stt_dumps(dict_a))
        return bytes_enter

    def _stt_dumps(self, data: dict) -> str:  # 斗鱼协议弄成str，记住一句话stt是个笨比，list和dict混着用会挂，设计协议的人笨比
        if isinstance(data, dict):
            return '/'.join([self._stt_dumps(key) + '@=' + self._stt_dumps(value) for key, value in data.items()]) + '/'
        if isinstance(data, str):
            return data.replace('@', '@A').replace('/', '@S')
        raise Exception('Dumps Error: Unexpected value type')

    @staticmethod
    def _stt_loads(data: str) -> dict:  # 仅解析dict
        data = data.replace('@=', '":"').replace('/', '","')
        data = data.replace('@A', '@').replace('@S', '/')
        msg = json.loads(f'{{"{data[:-2]}}}')
        return msg

    def _encapsulate(self, str_body, is_send=True, len_header=12):
        body = str_body.encode('utf-8')
        end = b'\x00'
        len_data = len_header + len(body) + len(end) - 4  # 反正减了4，不知道原因
        type_data = 689 if is_send else 690
        header = self.header_struct.pack(len_data, len_data, type_data, 0)
        return header + body + end

    async def _read_datas(self):
        while True:
            datas = await self._conn.read_bytes()
            # 本函数对bytes进行相关操作，不特别声明，均为bytes
            if datas is None:
                return
            data_l = 0
            len_datas = len(datas)
            while data_l != len_datas:
                # 每片data都分为header和body，data和data可能粘连
                # data_l == header_l && next_data_l == next_header_l
                # ||header_l...header_r|body_l...body_r||next_data_l...
                tuple_header = self.header_struct.unpack_from(datas[data_l:])
                len_data, _, _, _ = tuple_header
                body_l = data_l + 12
                next_data_l = data_l + len_data + 4
                body = datas[body_l:next_data_l-1]  # 因为最后一个字节是无效0
                # 人气值(或者在线人数或者类似)以及心跳
                dict_body = self._stt_loads(body.decode('utf8'))
                print(body)
                print(dict_body)
                print()

                data_l = next_data_l

    @staticmethod
    def handle_danmu(body):
        print(body)
        return True

    async def reset_roomid(self, room_id):
        async with self._conn_lock:
            # not None是判断是否已经连接了的(重连过程中也可以处理)
            await self._conn.close()
            if self._task_main is not None:
                await self._task_main
            # 由于锁的存在，绝对不可能到达下一个的自动重连状态，这里是保证正确显示当前监控房间号
            self._room_id = room_id
            print(f'{self._area_id}号弹幕姬已经切换房间（{room_id}）')

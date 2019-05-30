import json
import random
import zlib
from struct import Struct

from client import Client
from conn import TcpConn


class TcpV2DanmuClient(Client):
    header_struct = Struct('>I2H2I')

    def __init__(
            self, room_id: int, area_id: int, loop=None):
        heartbeat = 30.0
        conn = TcpConn(
            url='tcp://broadcastlv.chat.bilibili.com:2243',
            receive_timeout=heartbeat + 10)
        super().__init__(
            area_id=area_id,
            conn=conn,
            heartbeat=heartbeat,
            loop=loop)
        self._room_id = room_id

        self._bytes_heartbeat = self._encapsulate(opt=2, str_body='')
        self._funcs_task.append(self._send_heartbeat)

    @property
    def room_id(self):
        return self._room_id

    @property
    def _hello(self):
        uid = random.randrange(100000000000000, 200000000000000)
        str_enter = f'{{"roomid":{self._room_id},"uid":{uid}, "protover":2}}'
        bytes_enter = self._encapsulate(opt=7, str_body=str_enter)
        return bytes_enter

    def _encapsulate(self, opt, str_body, len_header=16, ver=2, seq=1):
        body = str_body.encode('utf-8')
        len_data = len(body) + len_header
        header = self.header_struct.pack(len_data, len_header, ver, opt, seq)
        return header + body

    def parse_body(self, body: bytes, opt: int) -> bool:
        if opt == 3:
            # num_watching, = struct.unpack('!I', body)
            print(f'弹幕心跳检测{self._area_id}')
        # cmd
        elif opt == 5:
            if not self.handle_danmu(json.loads(body.decode('utf-8'))):
                return False
        # 握手确认
        elif opt == 8:
            print(f'{self._area_id}号弹幕监控进入房间（{self._room_id}）')
        else:
            print(body)
            return False
        return True

    async def _read_one(self) -> bool:
        header = await self._conn.read_bytes(16)
        # 本函数对bytes进行相关操作，不特别声明，均为bytes
        if header is None:
            return False

        # 每片data都分为header和body，data和data可能粘连
        # data_l == header_l && next_data_l == next_header_l
        # ||header_l...header_r|body_l...body_r||next_data_l...
        tuple_header = self.header_struct.unpack_from(header)
        len_data, len_header, ver, opt, seq = tuple_header

        len_body = len_data - len_header
        body = await self._conn.read_bytes(len_body)
        # 本函数对bytes进行相关操作，不特别声明，均为bytes
        if body is None:
            return False

        print(tuple_header)

        print(f'seq == {seq}  ver == {ver}')
        if seq == 0 and ver == 2:  # v2协议有混合，可能不成熟吧
            datas = zlib.decompress(body)
            print((len(body) + 16) / (len(datas) + 16))
            data_l = 0
            len_datas = len(datas)
            while data_l != len_datas:
                # 每片data都分为header和body，data和data可能粘连
                # data_l == header_l && next_data_l == next_header_l
                # ||header_l...header_r|body_l...body_r||next_data_l...
                tuple_header = self.header_struct.unpack_from(datas[data_l:])
                len_data, len_header, ver, opt, _ = tuple_header
                assert ver == 0 or ver == 2
                body_l = data_l + len_header
                next_data_l = data_l + len_data
                body = datas[body_l:next_data_l]
                # 人气值(或者在线人数或者类似)以及心跳
                if not self.parse_body(body, opt):
                    return False
                data_l = next_data_l
            return True
        else:
            return self.parse_body(body, opt)

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

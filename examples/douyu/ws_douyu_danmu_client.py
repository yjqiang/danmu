"""本代码参考了
https://github.com/IsoaSFlus/danmaku
https://github.com/littlecodersh/danmu
https://github.com/dust8/pystt
斗鱼弹幕服务器第三方接入协议v1.6.2.pdf
特此感谢。
"""
import json
from typing import Optional

from aiohttp import ClientSession

from danmu_abc import WsConn, Client
from .utils import PackType, Pack


class WsDanmuClient(Client):
    __slots__ = ('_room_id', '_pack_heartbeat')

    def __init__(
            self, room_id: int, area_id: int,
            session: Optional[ClientSession] = None, loop=None):
        heartbeat = 45.0
        conn = WsConn(
            url='wss://danmuproxy.douyu.com:8506',
            receive_timeout=heartbeat + 10,
            session=session)
        super().__init__(
            area_id=area_id,
            conn=conn,
            heartbeat=heartbeat,
            loop=loop)
        self._room_id = room_id

        dict_heartbeat = {'type': 'mrkl'}
        self._pack_heartbeat = Pack.pack(str_body=self._stt_dumps(dict_heartbeat), pack_type=PackType.SEND)

    @property
    def room_id(self):
        return self._room_id

    async def _one_hello(self) -> bool:
        dict_enter = {
            'type': 'loginreq',
            'room_id': str(self._room_id),
        }
        bytes_enter = Pack.pack(str_body=self._stt_dumps(dict_enter), pack_type=PackType.SEND)

        dict_a = {
            'type': 'joingroup',
            'rid': str(self._room_id),
            'gid': '-9999'
        }
        bytes_enter += Pack.pack(str_body=self._stt_dumps(dict_a), pack_type=PackType.SEND)

        return await self._conn.send_bytes(bytes_enter)

    async def _one_heartbeat(self) -> bool:
        return await self._conn.send_bytes(self._pack_heartbeat)

    @staticmethod
    def _stt_dumps(data: dict) -> str:  # 斗鱼协议弄成str，记住一句话stt是个笨比，list和dict混着用会挂，设计协议的人笨比
        if isinstance(data, dict):
            return '/'.join([f'{WsDanmuClient._stt_dumps(key)}@={WsDanmuClient._stt_dumps(value)}'
                             for key, value in data.items()]) + '/'
        if isinstance(data, str):
            return data.replace('@', '@A').replace('/', '@S')
        raise Exception('Dumps Error: Unexpected value type')

    @staticmethod
    def _stt_loads(data: str) -> dict:  # 仅解析dict
        data = data.replace('@=', '":"').replace('/', '","')
        data = data.replace('@A', '@').replace('@S', '/')
        msg = json.loads(f'{{"{data[:-2]}}}')
        return msg

    async def _one_read(self) -> bool:
        packs = await self._conn.read_bytes()
        if packs is None:
            return False
        for _, body in Pack.unpack(packs):
            if not self.handle_danmu(self._stt_loads(body.decode('utf8'))):
                return False
        return True

    def handle_danmu(self, body):
        print(f'{self._area_id} 号数据连接:', body)
        return True

    async def reset_roomid(self, room_id):
        async with self._opening_lock:
            # not None是判断是否已经连接了的(重连过程中也可以处理)
            await self._conn.close()
            if self._task_main is not None:
                await self._task_main
            # 由于锁的存在，绝对不可能到达下一个的自动重连状态，这里是保证正确显示当前监控房间号
            self._room_id = room_id
            print(f'{self._area_id} 号数据连接已经切换房间（{room_id}）')

import json
import random
import zlib

from danmu_abc import TcpConn, Client
from .utils import Header, Opt, Pack


class TcpV2DanmuClient(Client):
    __slots__ = ('_room_id', '_pack_heartbeat')

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

        self._pack_heartbeat = Pack.pack('', opt=Opt.HEARTBEAT, ver=2, seq=1)

    @property
    def room_id(self):
        return self._room_id

    async def _one_hello(self) -> bool:
        uid = random.randrange(100000000000000, 200000000000000)
        str_enter = f'{{"roomid":{self._room_id},"uid":{uid}, "protover":2}}'
        return await self._conn.send_bytes(Pack.pack(str_enter, opt=Opt.AUTH, ver=2, seq=1))

    async def _one_heartbeat(self) -> bool:
        return await self._conn.send_bytes(self._pack_heartbeat)

    async def _one_read(self) -> bool:
        header = await self._conn.read_bytes(Header.raw_header_size)
        if header is None:
            return False

        len_pack, len_header, ver, opt, _ = Header.unpack(header)

        len_body = len_pack - len_header
        body = await self._conn.read_bytes(len_body)
        if body is None:
            return False

        if ver == 2 and opt == Opt.SEND_MSG_REPLY:  # v2 协议有混合，可能不成熟吧(混合了0 2)
            print('v2')
            packs = zlib.decompress(body)
            for opt, body in Pack.unpack(packs):
                if not self.parse_body(body, opt):
                    return False
            return True
        else:
            return self.parse_body(body, opt)

    def parse_body(self, body: bytes, opt: int) -> bool:
        # 人气值(或者在线人数或者类似)以及心跳
        if opt == Opt.HEARTBEAT_REPLY:
            # num_watching, = struct.unpack('!I', body)
            print(f'{self._area_id} 号数据连接心跳检测')
            pass
        # cmd
        elif opt == Opt.SEND_MSG_REPLY:
            if not self.handle_danmu(json.loads(body.decode('utf-8'))):
                return False
        # 握手确认
        elif opt == Opt.AUTH_REPLY:
            print(f'{self._area_id} 号数据连接进入房间（{self._room_id}）')
        else:
            print('?????', body)
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

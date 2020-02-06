"""本代码参考了
https://github.com/BacooTang/huya-danmu
https://github.com/IsoaSFlus/danmaku
特此感谢。
"""
from typing import Optional
import re

from aiohttp import ClientSession

from client import Client
from conn import WsConn
from .utils import WSUserInfo, WebSocketCommand, EWebSocketCommandType, WSPushMessage, MessageNotice
from .tars.core import tarscore


class WsDanmuClient(Client):
    def __init__(
            self, room: str, area_id: int,
            session: Optional[ClientSession] = None, loop=None):
        heartbeat = 60.0
        conn = WsConn(
            url='wss://cdnws.api.huya.com',
            receive_timeout=heartbeat+10,
            session=session)
        super().__init__(
            area_id=area_id,
            conn=conn,
            heartbeat=heartbeat,
            loop=loop)
        self._room = room
        self._ayyuid = None
        self._topsid = None
        self._subsid = None

        self._pack_heartbeat = b'\x00\x03\x1d\x00\x00\x69\x00\x00\x00\x69\x10\x03\x2c\x3c\x4c\x56\x08\x6f\x6e\x6c\x69\x6e\x65\x75\x69\x66\x0f\x4f\x6e\x55\x73\x65\x72\x48\x65\x61\x72\x74\x42\x65\x61\x74\x7d\x00\x00\x3c\x08\x00\x01\x06\x04\x74\x52\x65\x71\x1d\x00\x00\x2f\x0a\x0a\x0c\x16\x00\x26\x00\x36\x07\x61\x64\x72\x5f\x77\x61\x70\x46\x00\x0b\x12\x03\xae\xf0\x0f\x22\x03\xae\xf0\x0f\x3c\x42\x6d\x52\x02\x60\x5c\x60\x01\x7c\x82\x00\x0b\xb0\x1f\x9c\xac\x0b\x8c\x98\x0c\xa8\x0c'

    async def _prepare_client(self) -> bool:
        url = f'https://m.huya.com/{self._room}'
        headers = {
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/79.0.3945.88 Mobile Safari/537.36'
        }
        async with ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                room_page = await resp.text()
                self._ayyuid = int(re.search(r"ayyuid: +'([0-9]+)'", room_page, re.MULTILINE).group(1))
                self._topsid = int(re.search(r"TOPSID += +'([0-9]+)'", room_page, re.MULTILINE).group(1))
                self._subsid = int(re.search(r"SUBSID += +'([0-9]+)'", room_page, re.MULTILINE).group(1))
        return True

    async def _one_hello(self) -> bool:
        ws_user_info = WSUserInfo()
        ws_user_info.lUid = self._ayyuid
        ws_user_info.lTid = self._topsid
        ws_user_info.lSid = self._subsid

        output_stream = tarscore.TarsOutputStream()
        ws_user_info.writeTo(output_stream)

        ws_command = WebSocketCommand()
        ws_command.iCmdType = EWebSocketCommandType.EWSCmd_RegisterReq
        ws_command.vData = output_stream.getBuffer()
        output_stream = tarscore.TarsOutputStream()
        ws_command.writeTo(output_stream)

        return await self._conn.send_bytes(output_stream.getBuffer())

    async def _one_heartbeat(self) -> bool:
        return await self._conn.send_bytes(self._pack_heartbeat)
        
    async def _one_read(self) -> bool:
        pack = await self._conn.read_bytes()

        if pack is None:
            return False

        return self.handle_danmu(pack)

    def handle_danmu(self, pack):
        # print(f'{self._area_id} 号数据连接:', pack)

        stream = tarscore.TarsInputStream(pack)
        command = WebSocketCommand()
        command.readFrom(stream)

        if command.iCmdType == EWebSocketCommandType.EWSCmdS2C_MsgPushReq:
            stream = tarscore.TarsInputStream(command.vData)
            msg = WSPushMessage()
            msg.readFrom(stream)
            # 仅实现了说话的弹幕
            if msg.iUri == 1400:
                stream = tarscore.TarsInputStream(msg.sMsg)
                msg = MessageNotice()
                msg.readFrom(stream)
                print(f'{self._area_id} 号数据连接:'
                      f' [{msg.tUserInfo.sNickName.decode("utf-8")}]: {msg.sContent.decode("utf-8")}')

        return True

    async def reset_roomid(self, room):
        async with self._opening_lock:
            # not None是判断是否已经连接了的(重连过程中也可以处理)
            await self._conn.close()
            if self._task_main is not None:
                await self._task_main
            # 由于锁的存在，绝对不可能到达下一个的自动重连状态，这里是保证正确显示当前监控房间号
            self._room = room
            print(f'{self._area_id} 号数据连接已经切换房间（{room}）')

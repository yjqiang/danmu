import asyncio
import struct
import json
import sys
import random


class BaseDanmuTcp():
    structer = struct.Struct('!I2H2I')

    def __init__(self, room_id, area_id, session=None):
        self._session = None
        self._reader = None
        self._writer = None
        
        self._area_id = area_id
        self._room_id = room_id
        # 建立连接过程中难以处理重设置房间问题
        self._conn_lock = asyncio.Lock()
        self._task_main = None
        self._waiting = None
        self._closed = False
        self._bytes_heartbeat = self._wrap_str(opt=2, str_body='')
    
    @property
    def room_id(self):
        return self._room_id
        
    def _wrap_str(self, opt, str_body, len_header=16, ver=1, seq=1):
        bytes_body = str_body.encode('utf-8')
        len_data = len(bytes_body) + len_header
        header = self.structer.pack(len_data, len_header, ver, opt, seq)
        return header + bytes_body

    async def _send_bytes(self, bytes_data):
        try:
            self._writer.write(bytes_data)
        except asyncio.CancelledError:
            return False
        except:
            print(sys.exc_info()[0])
            return False
        return True

    async def _read_bytes(self, n):
        bytes_data = None
        try:
            bytes_data = await asyncio.wait_for(
                self._reader.readexactly(n), timeout=35)
        except asyncio.TimeoutError:
            print('# 由于心跳包30s一次，但是发现35内没有收到任何包，说明已经悄悄失联了，主动断开')
            return None
        except:
            print(sys.exc_info()[0])
            return None
                
        return bytes_data
        
    async def _connect_tcp(self):
        try:
            url = 'livecmt-2.bilibili.com'
            port = 2243
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(url, port), timeout=3)
        except asyncio.TimeoutError:
            print('连接超时')
            return False
        except:
            print("连接无法建立，请检查本地网络状况")
            print(sys.exc_info()[0])
            return False
        print(f'{self._area_id}号弹幕监控已连接b站服务器')
        
        uid = random.randrange(100000000000000, 200000000000000)
        str_enter = f'{{"roomid":{self._room_id},"uid":{uid}}}'
        print(str_enter)
    
        bytes_enter = self._wrap_str(opt=7, str_body=str_enter)
        
        return await self._send_bytes(bytes_enter)
        
    async def _close_tcp(self):
        self._writer.close()
        self._writer.close()
        # py3.7 才有（妈的你们真的磨叽）
        # await self._writer.wait_closed()
        
    async def _heart_beat(self):
        try:
            while True:
                if not await self._send_bytes(self._bytes_heartbeat):
                    return
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            return
            
    async def _read_datas(self):
        while True:
            header = await self._read_bytes(16)
            # 本函数对bytes进行相关操作，不特别声明，均为bytes
            if header is None:
                return
            
            # 每片data都分为header和body，data和data可能粘连
            # data_l == header_l && next_data_l == next_header_l
            # ||header_l...header_r|body_l...body_r||next_data_l...
            tuple_header = self.structer.unpack_from(header)
            len_data, len_header, _, opt, _ = tuple_header
            
            len_body = len_data - len_header
            body = await self._read_bytes(len_body)
            # 本函数对bytes进行相关操作，不特别声明，均为bytes
            if body is None:
                return
            
            # 人气值(或者在线人数或者类似)以及心跳
            if opt == 3:
                # num_watching, = struct.unpack('!I', body)
                print(f'弹幕心跳检测{self._area_id}')
                pass
            # cmd
            elif opt == 5:
                if not self.handle_danmu(body):
                    return
            # 握手确认
            elif opt == 8:
                print(f'{self._area_id}号弹幕监控进入房间（{self._room_id}）')
            else:
                print(body)
                return
                
    def handle_danmu(self, body):
        return True
        
    async def run_forever(self):
        self._waiting = asyncio.Future()
        while not self._closed:
            print(f'正在启动{self._area_id}号弹幕姬')
            
            async with self._conn_lock:
                if self._closed:
                    break
                if not await self._connect_tcp():
                    continue
                self._task_main = asyncio.ensure_future(self._read_datas())
                task_heartbeat = asyncio.ensure_future(self._heart_beat())
            tasks = [self._task_main, task_heartbeat]
            _, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED)
            print(f'{self._area_id}号弹幕姬异常或主动断开，正在处理剩余信息')
            if not task_heartbeat.done():
                task_heartbeat.cancel()
            await self._close_tcp()
            await asyncio.wait(pending)
            print(f'{self._area_id}号弹幕姬退出，剩余任务处理完毕')
        self._waiting.set_result(True)
            
    async def reset_roomid(self, room_id):
        async with self._conn_lock:
            # not None是判断是否已经连接了的(重连过程中也可以处理)
            if self._writer is not None:
                await self._close_tcp()
            if self._task_main is not None:
                await self._task_main
            # 由于锁的存在，绝对不可能到达下一个的自动重连状态，这里是保证正确显示当前监控房间号
            self._room_id = room_id
            print(f'{self._area_id}号弹幕姬已经切换房间（{room_id}）')
            
    async def close(self):
        if not self._closed:
            self._closed = True
            async with self._conn_lock:
                if self._writer is not None:
                    await self._close_tcp()
            if self._waiting is not None:
                await self._waiting
            return True
        else:
            return False
        
        
class DanmuPrinter(BaseDanmuTcp):
    def handle_danmu(self, body):
        dic = json.loads(body.decode('utf-8'))
        cmd = dic['cmd']
        if cmd == 'DANMU_MSG':
            print(dic)
        return True

import asyncio
from typing import Optional, Callable
from abc import ABC, abstractmethod

from .conn import Conn


class Client(ABC):
    __slots__ = (
        '_loop', '_area_id', '_conn', '_opening_lock', '_waiting_end', '_waiting_pause', '_closed',
        '_heartbeat', '_task_main', '_funcs_task', '_logger_info'
    )

    def __init__(
            self, area_id: int, conn: Conn, heartbeat: float = 30.0, loop: asyncio.AbstractEventLoop = None,
            logger_info: Callable = print
    ):
        self._loop = asyncio.get_event_loop() if loop is None else loop
        self._logger_info = logger_info
         
        self._area_id = area_id
        self._conn = conn
            
        # 建立连接过程中难以处理重设置房间或断线等问题
        self._opening_lock = asyncio.Lock()
        self._waiting_end: Optional[asyncio.Future] = None
        self._waiting_pause: Optional[asyncio.Future] = None
        self._closed = False

        self._heartbeat = heartbeat  # 心跳间隔

        self._task_main = None
        # 除了 _job_main 和 _job_heartbeat
        self._funcs_task = []

    # 建立连接并且 _say_hello
    async def _job_open(self) -> bool:
        if await self._conn.open():
            return await self._one_hello()
        return False

    # 建立连接后进行一次 auth
    @abstractmethod
    async def _one_hello(self) -> bool:
        pass

    # 持续心跳
    async def _job_heartbeat(self) -> None:
        try:
            while True:
                if not await self._one_heartbeat():
                    return
                await asyncio.sleep(self._heartbeat)
        except asyncio.CancelledError:
            return

    # 发送一次心跳包
    @abstractmethod
    async def _one_heartbeat(self) -> bool:
        pass

    # 循环读取
    async def _job_main(self) -> None:
        while self._waiting_pause is None:
            if not await self._one_read():
                return

    # 读一次数据（完整数据包括头尾）
    @abstractmethod
    async def _one_read(self) -> bool:
        pass

    # 关闭当前连接，并非永久关闭！不包含 clean 工作等！
    async def _job_close(self) -> None:
        await self._conn.close()

    @staticmethod
    async def _prepare_client() -> bool:
        return True

    async def run_forever(self) -> None:
        self._waiting_end = self._loop.create_future()
        while not self._closed:
            self._logger_info(f'正在启动 {self._area_id} 号数据连接')
            if self._waiting_pause is not None:
                self._logger_info(f'暂停启动 {self._area_id} 号数据连接，等待 RESUME 指令')
                await self._waiting_pause
            
            async with self._opening_lock:
                if self._closed:
                    self._logger_info(f'{self._area_id} 号数据连接确认收到关闭信号，正在处理')
                    break
                # 未成功建立数据连接，循环重试
                if await self._prepare_client() and await self._job_open():
                    tasks = [self._loop.create_task(i()) for i in self._funcs_task]

                    self._task_main = self._loop.create_task(self._job_main())
                    tasks.append(self._task_main)

                    task_heartbeat = self._loop.create_task(self._job_heartbeat())
                    tasks.append(task_heartbeat)
                else:
                    continue
                
            _, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED)
            self._logger_info(f'{self._area_id} 号数据连接异常或主动断开，正在处理剩余信息')
            for i in pending:
                if i != self._task_main:
                    i.cancel()
            await self._job_close()
            if pending:
                await asyncio.wait(pending)
            self._logger_info(f'{self._area_id} 号数据连接退出，剩余任务处理完毕')
        await self._conn.clean()
        self._waiting_end.set_result(True)

    @property
    def paused(self) -> bool:
        return self._waiting_pause is not None

    # 非主动 cancel，而是静静等下一个主循环
    def pause(self) -> None:
        if self._waiting_pause is None:
            self._waiting_pause = self._loop.create_future()
            
    def resume(self) -> None:
        if self._waiting_pause is not None:
            self._waiting_pause.set_result(True)
            self._waiting_pause = None
            
    async def close_and_clean(self) -> bool:
        if not self._closed:
            self._closed = True
            async with self._opening_lock:
                await self._job_close()

            if self._waiting_end is not None:
                await self._waiting_end
            return True
        return False

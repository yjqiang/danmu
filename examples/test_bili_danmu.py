import asyncio

from examples.bili.tcp_bili_danmu_client import TcpDanmuClient
from examples.bili.tcp_v2_bili_danmu_client import TcpV2DanmuClient
from examples.bili.ws_bili_danmu_client import WsDanmuClient
from examples.bili.ws_v2_bili_danmu_client import WsV2DanmuClient


room_id = 21721813
area_id = 0


async def test_danmu_client(client):
    tasks = []
    for _ in range(1):
        connection = client(room_id, area_id)
        tasks.append(asyncio.create_task(connection.run_forever()))
    await asyncio.wait(tasks)


async def test_tcp_danmu_client():
    await test_danmu_client(TcpDanmuClient)


async def test_tcp_v2_danmu_client():
    await test_danmu_client(TcpV2DanmuClient)
    
    
async def test_ws_danmu_client():
    await test_danmu_client(WsDanmuClient)


async def test_ws_v2_danmu_client():
    await test_danmu_client(WsV2DanmuClient)


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(test_tcp_danmu_client())
loop.close()

import asyncio
from tcp_danmu_client import TcpDanmuClient
from ws_danmu_client import WsDanmuClient


room_id = 23058
area_id = 0


async def test_danmu_client(Client):
    connection = Client(room_id, area_id)
    asyncio.ensure_future(connection.run_forever())
    await asyncio.sleep(20)
    await connection.reset_roomid(7734200)
    print('RESTED')
    await asyncio.sleep(20)
    await connection.close()
    print('END')
    
    await asyncio.sleep(1000)


async def test_tcp_danmu_client():
    await test_danmu_client(TcpDanmuClient)
    
    
async def test_ws_danmu_client():
    await test_danmu_client(WsDanmuClient)


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(test_ws_danmu_client())
loop.close()

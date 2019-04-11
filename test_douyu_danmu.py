import asyncio
from tcp_douyu_danmu_client import TcpDanmuClient
from ws_douyu_danmu_client import WsDanmuClient


room_id = 952595
area_id = 0


async def test_danmu_client(client):
    connection = client(room_id, area_id)
    asyncio.ensure_future(connection.run_forever())
    await asyncio.sleep(20)
    await connection.reset_roomid(952595)
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
loop.run_until_complete(test_tcp_danmu_client())
loop.close()

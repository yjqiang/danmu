import asyncio
from tcp_bili_danmu_client import TcpDanmuClient
from ws_bili_danmu_client import WsDanmuClient


room_id = 23058
area_id = 0


async def test_danmu_client(client):
    connection = client(room_id, area_id)
    asyncio.ensure_future(connection.run_forever())
    await asyncio.sleep(20)
    await connection.reset_roomid(55)
    await asyncio.sleep(30)
    print('RESTED')
    connection.pause()
    await asyncio.sleep(20)
    await connection.reset_roomid(23058)
    await asyncio.sleep(200)
    print('resume')
    connection.resume()
    await asyncio.sleep(200)
    print('close')
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

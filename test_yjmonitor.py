import asyncio
from tcp_yjmonitor_client import TcpYjMonitorClient
# from ws_monitor_client import WsYjMonitorClient


key='MO[W+f[dMX90m`5,'
url = 'tcp://192.168.0.107:8002'
area_id = 0


async def test_yjmonitor_client(Client):
    connection = Client(
        key=key,
        url=url,
        area_id=area_id)
    asyncio.ensure_future(connection.run_forever())
    await asyncio.sleep(2000)
    await connection.close()
    print('END')
    
    await asyncio.sleep(1000)


async def test_tcp_yjmonitor_client():
    await test_yjmonitor_client(TcpYjMonitorClient)
    
    
async def test_ws_yjmonitor_client():
    await test_yjmonitor_client(TcpYjMonitorClient)


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(test_tcp_yjmonitor_client())
loop.close()

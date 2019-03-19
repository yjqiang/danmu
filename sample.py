import asyncio
import blivedm_ws
import blivedm_tcp
import blivedm_ws_v2


class DanmuPrinter0(blivedm_ws.BaseDanmu):
    def handle_danmu(self, dict_danmu):
        cmd = dict_danmu['cmd']
        # print(cmd)
        if cmd == 'DANMU_MSG':
            info = dict_danmu['info']
            print(f'({info[2][0]}){info[2][1]}:{info[1]}')
        return True

                
class DanmuPrinter1(blivedm_tcp.BaseDanmu):
    def handle_danmu(self, dict_danmu):
        cmd = dict_danmu['cmd']
        # print(cmd)
        if cmd == 'DANMU_MSG':
            info = dict_danmu['info']
            print(f'({info[2][0]}){info[2][1]}:{info[1]}')
        return True
        

class DanmuPrinter2(blivedm_ws_v2.BaseDanmu):
    def handle_danmu(self, dict_danmu):
        cmd = dict_danmu['cmd']
        # print(cmd)
        if cmd == 'DANMU_MSG':
            info = dict_danmu['info']
            print(f'({info[2][0]}){info[2][1]}:{info[1]}')
        return True


async def test0():
    connection = DanmuPrinter0(7734200, 0)
    await connection.run_forever()

async def test1():
    connection = DanmuPrinter1(7734200, 0)
    await connection.run_forever()
    
async def test2():
    connection = DanmuPrinter2(7734200, 0)
    await connection.run_forever()


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test0())
    loop.close()


if __name__ == '__main__':
    main()

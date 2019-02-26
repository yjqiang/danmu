# -*- coding: utf-8 -*-

import json
import asyncio
import blivedm_ws
import blivedm_tcp


class DanmuPrinter0(blivedm_ws.BaseDanmu):
    def handle_danmu(self, body):
        dic = json.loads(body.decode('utf-8'))
        cmd = dic['cmd']
        if cmd == 'DANMU_MSG':
            info = dic['info']
            print(f'({info[2][0]}){info[2][1]}:{info[1]}')
        return True

                
class DanmuPrinter1(blivedm_tcp.BaseDanmu):
    def handle_danmu(self, body):
        dic = json.loads(body.decode('utf-8'))
        cmd = dic['cmd']
        if cmd == 'DANMU_MSG':
            info = dic['info']
            print(f'({info[2][0]}){info[2][1]}:{info[1]}')
        return True

async def test1():
    connection = DanmuPrinter0(23058, 0)
    await connection.run_forever()

async def test2():
    connection = DanmuPrinter1(23058, 0)
    await connection.run_forever()


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test2())
    loop.close()


if __name__ == '__main__':
    main()

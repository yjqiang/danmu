# -*- coding: utf-8 -*-

import asyncio
from blivedm_ws import DanmuPrinter

async def test1():
    connection = DanmuPrinter(23058, 0)
    await connection.run_forever()

async def test2():
    connection = DanmuPrinter(23058, 0)
    await connection.run_forever()


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test1())
    loop.close()


if __name__ == '__main__':
    main()

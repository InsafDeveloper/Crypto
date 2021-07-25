from datetime import datetime

import aiohttp
import asyncio


async def print_after(time):
    await asyncio.sleep(time)
    return time


async def main():
    startTime = datetime.now()
    task1 = print_after(5)
    task2 = print_after(7)
    tasks = []
    tasks.append(task1)
    tasks.append(task2)
    l = await asyncio.gather(*tasks)
    print(l)
    print(datetime.now() - startTime)


asyncio.run(main())

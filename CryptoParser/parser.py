import asyncio

from datetime import datetime

import aiogram
from aiogram.dispatcher.filters import Command
from aiogram.utils import executor

import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, AllowedUpdates, ContentType
from ConfigData import channel_chat_id_bot_status

from BanksCorridor import BanksCorridor

usdt_course_status = "default"
usdt_course = 0


# Configure logging
from ConfigData import telegram_bot_token
from GeneralFunctions import bestchange_get_courses, binance_get_courses
from TriangleCorridor import TriangleCorridor

logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=telegram_bot_token)
dp = Dispatcher(bot)

async def main_and_poll():
    tasks = [asyncio.create_task(main()),asyncio.create_task(poll())]
    await asyncio.gather(*tasks)

@dp.message_handler()
async def echo(message: types.Message):
    global usdt_course
    global usdt_course_status

    if message.chat.id == -1001342192085:
        if "usdt=" in message.text:
            try:
                parametr = message.text.split("usdt=")[1]
                if parametr == "default":
                    usdt_course_status = "default"
                    await message.answer(text="USDT course set to spot course")
                else:
                    usdt_course_status = "changed"
                    usdt_course = float(parametr)
                    await message.answer(text="USDT course set to special course - " + str(usdt_course))
            except Exception:
                print("Ошибка в вводе сбщ")


async def poll():
    while True:
        try:
            await dp.start_polling()
        except Exception:
            print("Ошибка в Poll'e")


async def main():
    proxies = [None,
               # 'http://your_user:your_password@your_proxy_url:your_proxy_port' http://6cZagz:7hhod8@81.177.3.50:17869
               'http://9LaoVq:u6ETwd@46.3.22.205:8000'
               # http://ysuAdv:fV9jfX@81.177.3.50:17867
               # http://tXCvyH:pjFE1A@217.29.53.104:39308
                ]
               # 'http://temaartemii666_gmail:590684d6c4@45.134.28.99:30001',
               # 'http://temaartemii666_gmail:590684d6c4@86.62.16.149:30001',
               # 'http://temaartemii666_gmail:590684d6c4@86.62.19.13:30001']
    proxy_counter = 0
    while True:
        try:
            startTime = datetime.now()

            best_courses = await download_best_courses(proxies[proxy_counter])  # [[[{"qiwi"}, {"tink"}, {"sber"}], ["triangle"]], {"binance"}]
            proxy_counter += 1
            if proxy_counter == 2:
                proxy_counter = 0

            bestchange_banks_courses = best_courses[0][0]  # [{"qiwi"}, {"tink"}, {"sber"}]
            bestchange_triangle_courses = best_courses[0][1]  # ["triangle"]
            binance_courses = best_courses[1]  # {binance}

            if usdt_course_status == "changed":
                binance_courses["USDT"] = usdt_course
            print("USDT COURSE ============" + str(binance_courses["USDT"]))
            if bestchange_banks_courses is not None and binance_courses is not None:
                bank_corridor = BanksCorridor(bestchange_banks_courses, binance_courses, bot)
                await bank_corridor.send_checked_profits()

            if bestchange_triangle_courses is not None and binance_courses is not None:
                triangle_corridor = TriangleCorridor(bestchange_triangle_courses, binance_courses, bot)
                await triangle_corridor.send_checked_profits()

            print("------------------------------------------------------------------")
            print("12312983123128 ОБЩЕЕ ВРЕМЯ: " + str(datetime.now() - startTime))
            print("proxy - " + str(proxy_counter) + str(proxies[proxy_counter-1]))
            print("------------------------------------------------------------------")
            await bot.send_message(chat_id=channel_chat_id_bot_status,
                                        text="Full work time is " + str(datetime.now() - startTime),
                                        parse_mode=ParseMode.MARKDOWN)
        except:
            print("Ошибка в коде")


async def download_best_courses(proxy):
    tasks = [asyncio.create_task(bestchange_get_courses(proxy)), asyncio.create_task(binance_get_courses())]
    return await asyncio.gather(*tasks)

if __name__ == '__main__':

    # executor.start_polling(dp, skip_updates=True)

    # isEntered = False
    # bank_corridor = BanksCorridor(None, None, None)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_and_poll())
import io
from zipfile import ZipFile

import aiohttp
import asyncio
import copy

from datetime import datetime

from config import pay_method_ids, pay_method_names, crypto_ids, crypto_names, bestchange_best_courses_layout, \
    binance_courses_to_usdt_layout, telegram_bot_token, channel_chat_id_plus1, channel_chat_id_under1, bestchange_links, \
    binance_links

import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode
from aiogram.utils.markdown import link


async def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Initialize bot and dispatcher
    bot = Bot(token=telegram_bot_token)
    dp = Dispatcher(bot)

    while True:
        try:
            startTime = datetime.now()
            tasks = [asyncio.create_task(bestchange_get_courses()), asyncio.create_task(binance_get_courses())]
            L = await asyncio.gather(*tasks)
            print(L)

            if L[0] is not None and L[1] is not None:
                profit_texts = await check_profit(L[0], L[1])
                if len(profit_texts) != 0:
                    await telegram_send_messages(profit_texts=profit_texts, bot=bot)

            print("общее время: " + str(datetime.now() - startTime))
        except Exception:
            print("Ошибка!")


async def telegram_send_messages(profit_texts, bot):
    profits_under1 = ""
    profits_plus1 = ""
    for profit_text in profit_texts:
        try:
            profit = float(profit_text.split("Profit: ")[1][:-2])
            if 0.5 < profit < 1:
                profits_under1 += profit_text + "\n\n"
            elif profit > 1:
                profits_plus1 += profit_text + "\n\n"
        except Exception:
            print("Ошибка: получение профитов")
    try:
        if profits_under1 != "":
            await telegram_send_messages_to_under1(profits_under1, bot)
        if profits_plus1 != "":
            await telegram_send_messages_to_plus1(profits_plus1, bot)
    except Exception:
        print("Ошибка: отправка сообщения в бот")


async def telegram_send_messages_to_under1(profit_text, bot):
    await bot.send_message(channel_chat_id_under1, text=profit_text, parse_mode=ParseMode.MARKDOWN)


async def telegram_send_messages_to_plus1(profit_text, bot):
    await bot.send_message(channel_chat_id_plus1, text=profit_text, parse_mode=ParseMode.MARKDOWN)


async def check_profit(bestchange_best_courses, binance_courses):
    usdt_course = binance_courses["USDT"]
    profit_texts = []
    for crypto_id in bestchange_best_courses:
        crypto_name = crypto_names[crypto_id]
        bestchange_pay_method = pay_method_names[bestchange_best_courses[crypto_id][0]]

        bestchange_price = bestchange_best_courses[crypto_id][2]
        binance_price = binance_courses[crypto_name]

        cross_course = bestchange_price / binance_price
        print(crypto_name + str(cross_course) + "   " + str(usdt_course))

        # '[<Ваш текст>](<Ссылка>)'

        if cross_course < usdt_course:
            profit = round((usdt_course / cross_course - 1) * 100, 2)
            if profit > 0.5:
                text = f"{link('Bestchange', bestchange_links[bestchange_pay_method][crypto_name])}: {bestchange_pay_method} -> {crypto_name} | Отдаем {bestchange_price} = Получаем 1 {crypto_name}\n" \
                       f"{link('Binance', binance_links[crypto_name])}: {crypto_name} -> USDT | Отдаем 1 {crypto_name} = Получаем {binance_price} USDT\n" \
                       f"Cross-Course для USDT = {cross_course}\n" \
                       f"{link('Binance-Course', binance_links['USDT'])} для USDT = {usdt_course}\n" \
                       f"Profit: {profit}%\n"

                profit_texts.append(text)
    return profit_texts


async def bestchange_get_courses():
    try:
        bm_rates = await bestchange_get_bmrates()
    except Exception:
        print("Ошибка в получении файла bm_rates.dat")
    else:
        try:
            bestchange_best_courses = await bestchange_get_best_courses(bm_rates)
        except Exception:
            print("Ошибка в получении наилучших курсов")
        else:
            return bestchange_best_courses


async def bestchange_get_bmrates():  # получение и разархивироание файла bm_rates.dat, содержащее все текущие курсы
    try:

        startTime = datetime.now()
        async with aiohttp.ClientSession() as session:
            async with session.get("http://api.bestchange.ru/info.zip") as resp:
                print("время загрузки зип: " + str(datetime.now() - startTime))
                print("ZIP DOWNLOADED SUCCESFUL")
                content = await resp.text(encoding="latin-1")  # 8 sec
                print("время resp зип: " + str(datetime.now() - startTime))
                zipFile1 = io.BytesIO(bytes(content, encoding="latin-1"))
                print("время io.bytes: " + str(datetime.now() - startTime))
                with ZipFile(zipFile1) as archive:
                    print("время открытия зип: " + str(datetime.now() - startTime))
                    print("ARCHIVE OPENED SUCCESFUL")
                    for member in archive.infolist():
                        if member.filename == "bm_rates.dat":
                            return await open_bmrates(archive, member)
    except Exception:
        print("Ошибка в загрузке или открытии ZIP-файла")


async def open_bmrates(archive, member):  # открытие bm_rates.dat и конвер в список состоящий из курсов
    try:
        startTime = datetime.now()
        bm_rates = str(archive.read(member))[2:-1].replace("\\n", "\n").split('\n')
    except Exception:
        print("Ошибка: открыте bm_rates.dat в ZIP с BestChange")
    else:
        print("время открытия бм рэйтс: " + str(datetime.now() - startTime))
        return bm_rates


async def bestchange_get_best_courses(bm_rates):  # парсинг курсов, нахождение наилучшего для каждой криптовалюты
    startTime = datetime.now()
    bestchange_best_courses = copy.deepcopy(bestchange_best_courses_layout)
    for course in bm_rates:
        try:
            course = course.split(';')
            currency_give_id = course[0]
            currency_get_id = course[1]
            platform_id = course[2]
            course_give = float(course[3])
            course_get = float(course[4])

            if course_get != 1.0:
                course_give = 1.0 / course_get

            if currency_give_id in pay_method_ids.values() and currency_get_id in crypto_ids.values():
                if course_give < bestchange_best_courses[currency_get_id][2]:
                    bestchange_best_courses[currency_get_id][0] = currency_give_id
                    bestchange_best_courses[currency_get_id][1] = platform_id
                    bestchange_best_courses[currency_get_id][2] = course_give
        except Exception:
            print("Ошибка: парсинг данных из " + str(course) + "в bm_rates.dat")
    print("время парсинга BESTCHANGE: " + str(datetime.now() - startTime))
    return bestchange_best_courses


async def binance_get_courses():
    startTime = datetime.now()
    binance_courses_to_usdt = copy.deepcopy(binance_courses_to_usdt_layout)
    tasks = []
    async with aiohttp.ClientSession() as session:
        for element in crypto_names.values():
            task = asyncio.create_task(binance_get_course_task(element, "USDT", session))
            tasks.append(task)
        task = asyncio.create_task(binance_get_course_task("USDT", "RUB", session))
        tasks.append(task)
        l = await asyncio.gather(*tasks)

    for crypto in l:
        crypto_name, price = crypto.split(" = ")[0], float(crypto.split(" = ")[1])
        binance_courses_to_usdt[crypto_name] = price

    print("время парсинга BINANCE: " + str(datetime.now() - startTime))
    return binance_courses_to_usdt


async def binance_get_course_task(element1, element2, session):
    binance_url = f'https://api.binance.com/api/v3/ticker/price?symbol={element1}{element2}'
    async with session.get(binance_url) as resp:
        coin = await resp.json()
        crypto_name = str(coin['symbol']).replace(element2, '')
        price = coin["price"]
        #               print(crypto_name + ' = ' + price)
        return crypto_name + ' = ' + price


class Closer:
    '''Менеджер контекста для автоматического закрытия объекта вызовом метода close
    в with-выражении.'''

    def __init__(self, obj):
        self.obj = obj

    async def __aenter__(self):
        return self.obj  # привязка к активному объекту with-блока

    async def __aexit__(self, exception_type, exception_val, trace):
        try:
            self.obj.close()
        except AttributeError:  # у объекта нет метода close
            print('Not closable.')
            return True  # исключение перехвачено


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

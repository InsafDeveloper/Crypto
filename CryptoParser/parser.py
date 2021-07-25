import io
from zipfile import ZipFile

import aiohttp
import asyncio
import copy

from datetime import datetime

from config import pay_method_ids, pay_method_names, crypto_ids, crypto_names, bestchange_best_courses_layout, \
    binance_courses_to_usdt_layout


async def main(beginning_sleep):
    startTime = datetime.now()
    await asyncio.sleep(beginning_sleep)
    while True:
        #try:
            tasks = [asyncio.create_task(bestchange_get_courses()), asyncio.create_task(binance_get_courses())]
            L = await asyncio.gather(*tasks)
            print(L)
            print("общее время: " + str(datetime.now() - startTime))
        #except Exception:
        #    print("Ошибка!")


async def check_profit():
    pass


async def bestchange_get_courses():
    #try:
        bm_rates = await bestchange_get_bmrates()
    #except Exception:
    #    print("Ошибка в получении файла bm_rates.dat")
    #else:
    #    try:
        bestchange_best_courses = await bestchange_get_best_courses(bm_rates)
    #    except Exception:
    #        print("Ошибка в получении наилучших курсов")
    #    else:
        return bestchange_best_courses

class Closer:
    '''Менеджер контекста для автоматического закрытия объекта вызовом метода close
    в with-выражении.'''

    def __init__(self, obj):
        self.obj = obj

    async def __aenter__(self):
        return self.obj # привязка к активному объекту with-блока

    async def __aexit__(self, exception_type, exception_val, trace):
        try:
           self.obj.close()
        except AttributeError: # у объекта нет метода close
           print('Not closable.')
           return True # исключение перехвачено

async def bestchange_get_bmrates():  # получение и разархивироание файла bm_rates.dat, содержащее все текущие курсы
    #try:

        startTime = datetime.now()
        async with aiohttp.ClientSession() as session:
            async with session.get("http://api.bestchange.ru/info.zip") as resp:
                print("время загрузки зип: " + str(datetime.now() - startTime))
                print("ZIP DOWNLOADED SUCCESFUL")
                content = await resp.text(encoding="latin-1") # 8 sec
                print("время resp зип: " + str(datetime.now() - startTime))
                zipFile = io.BytesIO(bytes(content, encoding="latin-1"))
                print("время io.bytes: " + str(datetime.now() - startTime))
                with ZipFile(zipFile) as archive:
                    print("время открытия зип: " + str(datetime.now() - startTime))
                    print("ARCHIVE OPENED SUCCESFUL")
                    for member in archive.infolist():
                        if member.filename == "bm_rates.dat":
                            return await open_bmrates(archive, member)
    #except Exception:
    #    print("Ошибка в загрузке или открытии ZIP-файла")


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
        crypto_name, price = crypto.split(" = ")[0], crypto.split(" = ")[1]
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

async def general_main(beginning_sleep):  # чем больше время, тем старее информация
    tasks = []
    for i in range(int(8/beginning_sleep)+1):
        task = asyncio.create_task(main(beginning_sleep*i))
        tasks.append(task)
    L = await asyncio.gather(*tasks)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(general_main(2))

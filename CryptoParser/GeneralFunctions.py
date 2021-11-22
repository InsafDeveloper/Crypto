import asyncio
import copy
import io
from datetime import datetime
from zipfile import ZipFile

import aiohttp


from ConfigData import bestchange_best_triangle_courses_layout, binance_courses_to_usdt_layout, crypto_names, \
    bestchange_best_courses_layout, crypto_ids, banned_triangle_platforms_for_all_cryptos, \
    banned_triangle_platforms_for_special_cryptos, pay_method_ids, banned_bank_platforms_for_all_cryptos, \
    banned_bank_platforms_for_special_cryptos


async def binance_get_courses():  # ПОЛУЧЕНИЕ КУРСОВ КРИПТОВАЛЮТ НА BINANCE
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


async def bestchange_get_courses(proxy):
    try:
        bm_rates = await bestchange_get_bmrates(proxy)
    except Exception:
        print("Ошибка в получении файла bm_rates.dat")
    else:
        try:
            bestchange_best_courses = await bestchange_get_best_courses_for_rub(
                bm_rates)  # [[{"qiwi"}, {"tink"}, {"sber"}], ["c-c"]], {"binance"}]
        except Exception:
            print("Ошибка в получении наилучших курсов")
        else:
            return bestchange_best_courses


async def bestchange_get_bmrates(proxy):  # получение и разархивироание файла bm_rates.dat, содержащее все текущие курсы
    try:
        startTime = datetime.now()
        async with aiohttp.ClientSession() as session:
            async with session.get("http://api.bestchange.ru/info.zip", proxy=proxy) as resp:
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
    except Exception as ex:
        print("Ошибка в загрузке или открытии ZIP-файла" + str(ex))


async def open_bmrates(archive, member):  # открытие bm_rates.dat и конвер в список состоящий из курсов
    try:
        startTime = datetime.now()
        bm_rates = str(archive.read(member))[2:-1].replace("\\n", "\n").split('\n')
    except Exception:
        print("Ошибка: открыте bm_rates.dat в ZIP с BestChange")
    else:
        print("время открытия бм рэйтс: " + str(datetime.now() - startTime))
        return bm_rates


async def bestchange_get_best_courses_for_rub(
        bm_rates):  # парсинг курсов, нахождение наилучшего для каждой криптовалюты за рубль(киви, тинькофф, сбер)
    startTime = datetime.now()

    bestchange_best_courses_qiwi = copy.deepcopy(bestchange_best_courses_layout)
    bestchange_best_courses_tinkoff = copy.deepcopy(bestchange_best_courses_layout)
    bestchange_best_courses_sberbank = copy.deepcopy(bestchange_best_courses_layout)
    bestchange_triangle_courses = copy.deepcopy(bestchange_best_triangle_courses_layout)

    banks_best_courses = {
        "63":  bestchange_best_courses_qiwi,
        "105": bestchange_best_courses_tinkoff,
        "42": bestchange_best_courses_sberbank
    }

    for position in bm_rates:
        try:
            position = position.split(';')
            currency_give_id = position[0]
            currency_get_id = position[1]
            platform_id = position[2]
            course_give = float(position[3])
            course_get = float(position[4])


            if await check_for_triangle_corridor_ability(currency_give_id, currency_get_id, platform_id):
                if course_get == 1.0:
                    course_get, course_give = 1.0 / course_give, 1.0
                if course_get > bestchange_triangle_courses[currency_give_id][currency_get_id]:
                    bestchange_triangle_courses[currency_give_id][currency_get_id] = course_get

            if course_get != 1.0:
                course_give, course_get = 1.0 / course_get, 1.0

            if await check_for_bank_corridor_ability(currency_give_id, currency_get_id, platform_id):
                if course_give < banks_best_courses[currency_give_id][currency_get_id][2]:
                    banks_best_courses[currency_give_id][currency_get_id][0] = currency_give_id
                    banks_best_courses[currency_give_id][currency_get_id][1] = platform_id
                    banks_best_courses[currency_give_id][currency_get_id][2] = course_give


        except Exception as a:
            print("Ошибка: парсинг данных из " + str(a) + "в bm_rates.dat")
    print("время парсинга BESTCHANGE: " + str(datetime.now() - startTime))
    bestchange_best_courses = [banks_best_courses["63"], banks_best_courses["105"],
                               banks_best_courses["42"]]

    bestchange_courses = [bestchange_best_courses, bestchange_triangle_courses]

    return bestchange_courses


async def check_for_triangle_corridor_ability(currency_give_id, currency_get_id, platform_id):
    if currency_give_id not in crypto_ids.values() or currency_get_id not in crypto_ids.values():
        return False
    if platform_id in banned_triangle_platforms_for_all_cryptos:
        return False
    if currency_give_id in banned_triangle_platforms_for_special_cryptos.keys():
        if platform_id in banned_triangle_platforms_for_special_cryptos[currency_give_id]:
            return False
    return True

async def check_for_bank_corridor_ability(currency_give_id, currency_get_id, platform_id):
    if currency_give_id not in pay_method_ids.values() or currency_get_id not in crypto_ids.values():
        return False
    if platform_id in banned_bank_platforms_for_all_cryptos:
        return False
    if currency_give_id in banned_bank_platforms_for_special_cryptos.keys():
        if platform_id in banned_bank_platforms_for_special_cryptos[currency_give_id]:
            return False
    return True


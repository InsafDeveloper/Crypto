from aiogram.types import ParseMode
from aiogram.utils.markdown import link
from ConfigData import crypto_names, pay_method_names, bestchange_links, binance_links, chat_id_qiwi_plus_one, \
    chat_id_qiwi_under_one, chat_id_tinkoff, chat_id_sberbank


class BanksCorridor:
    bestchange_banks_courses = None
    binance_courses = None
    usdt_course = None
    bot = None

    def __init__(self, bestchange_banks_courses, binance_courses, bot):
        self.bestchange_banks_courses = bestchange_banks_courses
        self.binance_courses = binance_courses
        self.usdt_course = binance_courses["USDT"]
        self.bot = bot

    async def init(self):
        print()

    async def send_checked_profits(self):
        profit_texts = await self.check_and_get_text_profits()  # {"":[],"":[],"":[]}
        await self.send_profits(profit_texts)

    async def check_and_get_text_profits(self):

        profit_texts = {
            "QIWI RUB": [],
            "Тинькофф RUB": [],
            "Сбербанк RUB": []
        }

        for pay_method_courses in self.bestchange_banks_courses:
            for crypto_id in pay_method_courses:
                try:
                    crypto_name = crypto_names[crypto_id]
                    bestchange_pay_method = pay_method_names[pay_method_courses[crypto_id][0]]
                    platform_id = pay_method_courses[crypto_id][1]
                    bestchange_price = pay_method_courses[crypto_id][2]
                    binance_price = self.binance_courses[crypto_name]
                    cross_course = bestchange_price / binance_price

                    if cross_course < self.usdt_course:
                        profit = round((self.usdt_course / cross_course - 1) * 100, 2)
                        if profit > 0.5:
                            text_to_send = await self.get_text_to_send(crypto_name, bestchange_pay_method,
                                                                 bestchange_price, binance_price, cross_course, profit, platform_id)
                            profit_texts[bestchange_pay_method].append(text_to_send)

                except Exception as a:
                    print("ОШИБКА В ПАРСИНГЕ КУРСОВ" + str(a))

        return profit_texts

    async def get_text_to_send(self, crypto_name, bestchange_pay_method, bestchange_price, binance_price, cross_course,
                         profit, platform_id):
        text = f"{link('Bestchange', bestchange_links[bestchange_pay_method][crypto_name])} [ID: {platform_id}]: {bestchange_pay_method} -> {crypto_name} | Отдаем {bestchange_price} = Получаем 1 {crypto_name}\n" \
               f"{link('Binance', binance_links[crypto_name])}: {crypto_name} -> USDT | Отдаем 1 {crypto_name} = Получаем {binance_price} USDT\n" \
               f"Cross-Course для USDT = {cross_course}\n" \
               f"{link('Binance-Course', binance_links['USDT'])} для USDT = {self.usdt_course}\n" \
               f"Profit: {profit}%\n"
        return text

    async def send_profits(self, profit_texts):
        for pay_method in pay_method_names.values():
            texts = profit_texts[pay_method]
            if len(texts) != 0:
                if pay_method == "QIWI RUB":
                    await self.send_qiwi_texts(profit_texts=texts)
                elif pay_method == "Тинькофф RUB":
                    await self.send_tinkoff(profit_texts=texts)
                elif pay_method == "Сбербанк RUB":
                    await self.send_sberbank(profit_texts=texts)

    async def send_qiwi_texts(self, profit_texts):
        profit_under1 = ""
        profit_plus1 = ""
        for profit_text in profit_texts:
            try:
                profit = float(profit_text.split("Profit: ")[1][:-2])
                if 0.5 < profit < 1:
                    profit_under1 += profit_text + "\n\n"
                elif profit > 1:
                    profit_plus1 += profit_text + "\n\n"
            except Exception:
                print("Ошибка: получение профитов")
        if profit_under1 != "":
            await self.send_qiwi_to_under_one(profit_under1)
        if profit_plus1 != "":
            await self.send_qiwi_to_plus_one(profit_plus1)


    async def send_qiwi_to_under_one(self, profit_text):
        await self.bot.send_message(chat_id=chat_id_qiwi_under_one,
                               text=profit_text,
                               parse_mode=ParseMode.MARKDOWN)

    async def send_qiwi_to_plus_one(self, profit_text):
        await self.bot.send_message(chat_id=chat_id_qiwi_plus_one,
                               text=profit_text,
                               parse_mode=ParseMode.MARKDOWN)

    async def send_tinkoff(self, profit_texts):
        profit_text = ""
        for text in profit_texts:
            profit_text += text + "\n\n"

        if profit_text != "":
            await self.bot.send_message(chat_id=chat_id_tinkoff,
                                   text=profit_text,
                                   parse_mode=ParseMode.MARKDOWN)

    async def send_sberbank(self, profit_texts):
        profit_text = ""
        for text in profit_texts:
            profit_text += text + "\n\n"

        if profit_text != "":
            await self.bot.send_message(chat_id=chat_id_sberbank,
                                   text=profit_text,
                                   parse_mode=ParseMode.MARKDOWN)

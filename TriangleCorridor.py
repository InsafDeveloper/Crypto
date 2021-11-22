from aiogram.utils.markdown import link

from aiogram.types import ParseMode

from ConfigData import crypto_ids, crypto_names, binance_links, bestchange_crypto_designations, chat_id_triangle


class TriangleCorridor:

    bestchange_triangle_courses = None
    binance_courses = None
    bot = None

    def __init__(self, bestchange_triangle_courses, binance_courses, bot):
        self.bestchange_triangle_courses = bestchange_triangle_courses
        self.binance_courses = binance_courses
        self.bot = bot

    async def send_checked_profits(self):
        profit_texts = await self.check_and_get_text_profits()
        await self.send_profits(profit_texts)

    async def check_and_get_text_profits(self):
        profit_texts = []
        for crypto_name in list(self.binance_courses.keys())[:-1]:  # USDT START-FINAL
            usdt_start_count = self.binance_courses[crypto_name]
            crypto_id = crypto_ids[crypto_name]
            bestchange_crypto_courses = self.bestchange_triangle_courses[crypto_id]

            for crypto_get_id in bestchange_crypto_courses.keys():
                bestchange_get_crypto_course = bestchange_crypto_courses[crypto_get_id]
                binance_crypto_usdt_course = self.binance_courses[crypto_names[crypto_get_id]]

                usdt_final_count = bestchange_get_crypto_course * binance_crypto_usdt_course
                profit = round((usdt_final_count / usdt_start_count - 1) * 100, 2)
                if profit > 0.95:
                    profit_texts.append(await self.get_text_to_send(crypto_name, crypto_get_id, usdt_start_count, bestchange_get_crypto_course,
                                                              usdt_final_count, binance_crypto_usdt_course, profit))

        return profit_texts

    async def get_text_to_send(self, crypto_name, crypto_get_id, usdt_start_count, bestchange_get_crypto_course,
                         usdt_final_count, binance_crypto_usdt_course, profit):
        print(crypto_name)
        text = f"Коридор USDT -> {crypto_name} -> {crypto_names[crypto_get_id]} -> USDT\n" \
               f"{link('Binance', binance_links[crypto_name])}: Отдаем {usdt_start_count} USDT -> получаем 1 {crypto_name}\n" \
               f"{link('Bestchange', f'https://www.bestchange.net/{bestchange_crypto_designations[crypto_name]}-to-{bestchange_crypto_designations[crypto_names[crypto_get_id]]}.html')} Отдаем 1 {crypto_name} -> получаем {bestchange_get_crypto_course} {crypto_names[crypto_get_id]}\n" \
               f"{link('Binance', binance_links[crypto_names[crypto_get_id]])}: Отдаем {bestchange_get_crypto_course} {crypto_names[crypto_get_id]} -> получаем {usdt_final_count} USDT по курсу {crypto_names[crypto_get_id]}/USDT = {binance_crypto_usdt_course}\n" \
               f"Profit: {profit}%"
        return text

    async def send_profits(self, profit_texts):
        if len(profit_texts) != 0:
            await self.send_triangle(profit_texts)

    async def send_triangle(self, profit_texts):
        profit_text = ""
        for i in range(len(profit_texts)):
            profit_text += profit_texts[i] + "\n\n"
            if i % 12 == 0 and i != 0:
                await self.bot.send_message(chat_id=chat_id_triangle,
                                       text=profit_text,
                                       parse_mode=ParseMode.MARKDOWN)
                profit_text = ""

        if profit_text != "":
            await self.bot.send_message(chat_id=chat_id_triangle,
                                   text=profit_text,
                                   parse_mode=ParseMode.MARKDOWN)
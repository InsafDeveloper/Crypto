import io
import zipfile

import copy

import requests
from config import pay_method_ids, pay_method_names, crypto_ids, crypto_names, best_courses_layout


def main():
    try:
        bm_rates = bestchange_get_bmrates()
        best_courses = parse_best_courses(bm_rates)
        print_best_courses(best_courses)
    except Exception:
        print("Ошибка!")


def bestchange_get_bmrates():  # получение и разархивироание файла bm_rates.dat, содержащее все текущие курсы
    try:
        r = requests.get("http://api.bestchange.ru/info.zip")
        print("ZIP GOT SUCCESFUL")
    except Exception:
        print("Ошибка: получение ZIP с BestChange")
    else:
        try:
            with r, zipfile.ZipFile(io.BytesIO(r.content)) as archive:
                for member in archive.infolist():
                    if member.filename == "bm_rates.dat":
                        return open_bmrates(archive, member)
        except Exception:
            print("Ошибка: разархивация ZIP BestChange")


def open_bmrates(archive, member):  # открытие bm_rates.dat и конвер в список состоящий из курсов
    try:
        bm_rates = str(archive.read(member))[2:-1].replace("\\n", "\n").split('\n')
    except Exception:
        print("Ошибка: открыте bm_rates.dat в ZIP с BestChange")
    else:
        return bm_rates


def parse_best_courses(bm_rates):  # парсинг курсов, нахождение наилучшего для каждой криптовалюты
    best_courses_in_file = copy.deepcopy(best_courses_layout)
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
                if course_give < best_courses_in_file[currency_get_id][2]:
                    best_courses_in_file[currency_get_id][0] = currency_give_id
                    best_courses_in_file[currency_get_id][1] = platform_id
                    best_courses_in_file[currency_get_id][2] = course_give
        except Exception:
            print("Ошибка: парсинг данных из " + str(course) + "в bm_rates.dat")

    return best_courses_in_file


def print_best_courses(best_courses):  # вывод лучших курсов
    for crypto_id in best_courses.keys():
        pay_method_name = pay_method_names[best_courses[crypto_id][0]]
        crypto_name = crypto_names[crypto_id]
        course = best_courses[crypto_id][2]

        print(
            pay_method_name + "->" + crypto_name + "\n" + "Отдаем " + str(course) + "RUB -> получаем 1 " + crypto_name)
        print()


while True:
    main()

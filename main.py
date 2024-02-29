import requests
from environs import Env
from terminaltables import AsciiTable


CITY_HH_ID = '1'
CITY_SJ_ID = 4
VACANCIES_QUANTITY = 100


def predict_rub_salary_hh(vacancy):
    if vacancy['salary'] and vacancy['salary']['currency'] == 'RUR':
        salary = predict_salary(vacancy['salary']['from'],
                                vacancy['salary']['to'])
        return salary


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] == 'rub':
        salary = predict_salary(vacancy['payment_from'],
                                vacancy['payment_to'])
        return salary


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        salary = (salary_from + salary_to) / 2
        return salary
    if not salary_from and salary_to:
        salary = salary_to * 0.8
        return salary
    if not salary_to and salary_from:
        salary = salary_from * 1.2
        return salary


def create_table(resourse_statistic, resourse_title):
    table_rows = [['Язык программирования', 'Вакансий найдено',
                   'Вакансий обработано', 'Средняя зарплата']]
    for language, statistic in resourse_statistic.items():
        table_rows.append([
            language.lower(),
            statistic['vacancies_found'],
            statistic['vacancies_processed'],
            statistic['average_salary']
        ])
    table = AsciiTable(table_rows, title=resourse_title)
    return table.table


def get_statistic_hh(languages):
    url_api_hh = 'https://api.hh.ru/vacancies'
    hh_statistics = {}
    for language in languages:
        language_vacancies = []
        pages_number = 1
        page = 0
        headers = {'User-Agent': 'api-test-agent'}
        while page < pages_number:
            params = {
                'page': page,
                'text': f'Программист {language}',
                'area': CITY_HH_ID,
                'per_page': VACANCIES_QUANTITY
            }
            page_response = requests.get(
                url_api_hh,
                params=params,
                headers=headers
            )
            page_response.raise_for_status()
            page_payload = page_response.json()
            pages_number = page_payload['pages']
            vacancies_page = page_payload['items']
            vacancies_found = page_payload['found']
            for vacancy in vacancies_page:
                language_vacancies.append(vacancy)
            page += 1
        vacancies_processed = 0
        total_salary = 0
        for language_vacancy in language_vacancies:
            rub_salary = predict_rub_salary_hh(language_vacancy)
            if not rub_salary:
                continue
            vacancies_processed += 1
            total_salary = total_salary + rub_salary
        if not vacancies_processed:
            average_salary = 0
        else:
            average_salary = int(total_salary / vacancies_processed)
        statistics = {
            'average_salary': average_salary,
            'vacancies_processed': vacancies_processed,
            'vacancies_found': vacancies_found
        }
        hh_statistics[language] = hh_statistics.get(language, statistics)
    return hh_statistics


def get_statistic_sj(languages, secret_key):
    url_api = 'https://api.superjob.ru/2.0/vacancies/?'
    sj_statistics = {}
    for language in languages:
        headers = {'X-Api-App-Id': secret_key}
        page = 0
        language_vacancies = []
        while True:
            params = {
                'catalogues': 'Разработка, программирование',
                'keyword': f'Программист {language}',
                'town': CITY_SJ_ID,
                'page': page
            }
            response = requests.get(url_api, headers=headers, params=params)
            response.raise_for_status()
            page_payload = response.json()
            vacancies_page = page_payload['objects']
            vacancies_found = page_payload['total']
            for vacancy in vacancies_page:
                language_vacancies.append(vacancy)
            page += 1
            if not len(vacancies_page):
                break
        vacancies_processed = 0
        total_salary = 0
        for language_vacancy in language_vacancies:
            rub_salary = predict_rub_salary_sj(language_vacancy)
            if not rub_salary:
                continue
            vacancies_processed += 1
            total_salary = total_salary + rub_salary
        if not vacancies_processed:
            average_salary = 0
        else:
            average_salary = int(total_salary / vacancies_processed)
        statistics = {
            'average_salary': average_salary,
            'vacancies_processed': vacancies_processed,
            'vacancies_found': vacancies_found
        }
        sj_statistics[language] = sj_statistics.get(language, statistics)
    return sj_statistics


def main():
    env = Env()
    env.read_env()
    secret_key = env.str('SECRET_KEY_SJ')
    languages = env.list('PROG_LANGUAGES')
    title_table_hh = 'HeadHunter Moscow'
    title_table_sj = 'SuperJob Moscow'
    try:
        print(create_table(get_statistic_hh(languages), title_table_hh))
        print(create_table(
            get_statistic_sj(languages, secret_key),
            title_table_sj)
        )
    except requests.exceptions.HTTPError:
        print('Ошибка HTTP, приложение завершило работу')


if __name__ == '__main__':
    main()

import requests
from environs import Env
from terminaltables import AsciiTable


def predict_rub_salary_hh(vacancie):
    if vacancie['salary'] is not None and vacancie['salary']['currency'] == 'RUR':
        salary = predict_salary(vacancie['salary']['from'], vacancie['salary']['to'])
        return salary


def predict_rub_salary_sj(vacancie):
    if vacancie['currency'] == 'rub':
        salary = predict_salary(vacancie['payment_from'], vacancie['payment_to'])
        return salary


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        salary = (salary_from + salary_to) / 2
        return salary
    else:
        if (salary_from == 0 or salary_from is None) and (salary_to is not (None or 0)):
            salary = salary_to * 0.8
            return salary
        if (salary_to == 0 or salary_to is None) and (salary_from is not (None or 0)):
            salary = salary_from * 1.2
            return salary


def create_table(dictionary, title):
    table_data = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for language, stat in dictionary.items():
        table_data.append([language.lower(), stat['vacancies_found'],
                           stat['vacancies_processed'], stat['average_salary']])
    table = AsciiTable(table_data, title=title)
    return table.table


def get_statistic_hh(languages):
    url_api_hh = 'https://api.hh.ru/vacancies'
    hh_statistics = {}
    for language in languages:
        language_vacancies = []
        pages_number = 1
        page = 0
        params = {
            'text': f'Программист {language}',
            'area': '1'
        }
        headers = {'User-Agent': 'api-test-agent'}
        response = requests.get(url_api_hh, params=params, headers=headers)
        vacancies_found = response.json()['found']
        while page < pages_number:
            params = {'page': page,
                      'text': f'Программист {language}',
                      'area': '1'
                      }
            page_response = requests.get(url_api_hh, params=params, headers=headers)
            page_response.raise_for_status()
            page_payload = page_response.json()
            pages_number = page_payload['pages']
            page_vacancies = page_payload['items']
            for vacancie in page_vacancies:
                language_vacancies.append(vacancie)
            if page == 14:
                break
            page += 1
        vacancies_processed = 0
        salary = 0
        for language_vacanscie in language_vacancies:
            if predict_rub_salary_hh(language_vacanscie) is None:
                continue
            vacancies_processed += 1
            salary = salary + predict_rub_salary_hh(language_vacanscie)
        average_salary = int(salary / vacancies_processed)
        statistics = dict(average_salary=average_salary, vacancies_processed=vacancies_processed,
                           vacancies_found=vacancies_found)
        hh_statistics[language] = hh_statistics.get(language, statistics)
    return hh_statistics


def get_statistic_sj(languages, secret_key):
    url_api = 'https://api.superjob.ru/2.0/vacancies/?'
    sj_statistics = {}
    headers = {'X-Api-App-Id': secret_key}
    for language in languages:
        params = {'catalogues': 'Разработка, программирование',
                  'keyword': f'{language}',
                  'town': 4,
                  }
        page = 0
        language_vacancies = []
        response = requests.get(url_api, params=params, headers=headers)
        vacancies_found = response.json()['total']
        while True:
            params = {'catalogues': 'Разработка, программирование',
                      'keyword': f'{language}',
                      'town': 4,
                      'page': page}
            response = requests.get(url_api, headers=headers, params=params)
            response.raise_for_status()
            page_vacancies = response.json()['objects']
            for vacancie in page_vacancies:
                language_vacancies.append(vacancie)
            page += 1
            if len(page_vacancies) == 0:
                break
        vacancies_processed = 0
        salary = 0
        for language_vacanscie in language_vacancies:
            if predict_rub_salary_sj(language_vacanscie) is None:
                continue
            vacancies_processed += 1
            salary = salary + predict_rub_salary_sj(language_vacanscie)
        if vacancies_processed == 0:
            average_salary = 0
        else:
            average_salary = int(salary / vacancies_processed)
        statistics = dict(vacancies_found=vacancies_found, vacancies_processed=vacancies_processed,
                           average_salary=average_salary)
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
        print(create_table(get_statistic_sj(languages, secret_key), title_table_sj))
    except requests.exceptions.HTTPError:
        print(f'Ошибка HTTP, приложение завершило работу')


if __name__ == '__main__':
    main()



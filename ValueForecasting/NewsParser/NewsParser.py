import datetime
import os

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry


class Parser:
    headers = {
        'Connection': 'close', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, '
                                             'like Gecko) Chrome/86.0.4240.111 Safari/537.36'
    }

    NAMES = ['date', 'news']

    @classmethod
    def parse_single_page(cls, theme, date_day, page_number):
        session = requests.Session()
        retry = Retry(connect=5, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('https://', adapter)

        output = []

        url = f'https://ria.ru/{theme}/{date_day}/?page={page_number}'
        page = session.get(url, headers=cls.headers)
        response = page.status_code
        if response == 200:
            soup = BeautifulSoup(page.text, 'html.parser')
            news = soup.find_all('a', class_='list-item__title color-font-hover-only')

            for i in range(len(news)):
                data = news[i]
                href = data['href']

                session1 = requests.Session()
                retry1 = Retry(connect=3, backoff_factor=0.5)
                adapter1 = HTTPAdapter(max_retries=retry1)
                session1.mount('https://', adapter1)
                page1 = requests.get(href, headers=cls.headers)
                response = page1.status_code
                if response == 200:
                    soup1 = BeautifulSoup(page1.text, 'html.parser')
                    text = soup1.find_all('div', class_='article__text')
                    text += soup1.find_all('div', class_='article_block')

                is_first = True
                for one_part in text:
                    if is_first:
                        splitted_str = one_part.text.split('. ', 1)
                        if len(splitted_str) > 1:
                            full_text = splitted_str[1]
                        else:
                            full_text = splitted_str[0]
                        is_first = False
                    else:
                        full_text += one_part.text
                if full_text != '':
                    output.append(full_text)

            # report_string = date_day + ' ' + theme + ' page ' + str(page_number) + ': parsed'
        # else:
            # report_string = date_day + ' ' + theme + ' page ' + str(page_number) + ': page not found'

        # print(report_string)
        return output, response

    @classmethod
    def parsing_daily_news(cls, date_day):

        response = 200
        page_number = 1
        text_list = []
        while response == 200:
            news_text, response = cls.parse_single_page(theme='economy', date_day=date_day,
                                                        page_number=page_number)
            if news_text:
                text_list.append(news_text)
            page_number += 1

        return text_list

    @classmethod
    def parse_news(cls, start_date: str, end_date: str):

        news_df = pd.DataFrame(columns=cls.NAMES)

        external_date_format = '%Y-%m-%d'
        date_format = '%Y%m%d'
        step = datetime.timedelta(days=1)
        start_date = datetime.datetime.strptime(start_date, external_date_format)
        end_date = datetime.datetime.strptime(end_date, external_date_format)

        date = start_date
        while date <= end_date:
            daily_news = cls.parsing_daily_news(date.strftime(date_format))
            news_df.loc[len(news_df.index)] = [date, daily_news]
            date += step

        # os.chdir('../Storage')
        # news_df.to_json('parsed_news_' + start_date.strftime(external_date_format) + '_' + end_date.strftime(
        #         external_date_format) + '.json')

        return news_df

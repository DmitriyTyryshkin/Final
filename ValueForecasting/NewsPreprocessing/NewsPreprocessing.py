import os
from pathlib import Path

import pandas as pd
import pymorphy2 as pymorphy2
import re
from ValueForecasting.NewsParser.NewsParser import Parser


class NewsPreprocessing:
    morph = pymorphy2.MorphAnalyzer()


    @classmethod
    def restrucurize(cls, old_list):
        new_list = []
        for page in range(len(old_list)):
            for news in range(len(old_list[page])):
                new_list.append(old_list[page][news])
        return new_list

    @classmethod
    def words_only(cls, text, regex_):
        try:
            return regex_.findall(text)
        except:
            return []

    @classmethod
    def lemmatize(cls, text):
        try:
            return " ".join([cls.morph.parse(w)[0].normal_form for w in text])
        except:
            return " "

    @classmethod
    def clean_text(cls, text, regex_):
        return cls.lemmatize(cls.words_only(text, regex_))

    @classmethod
    def cleaner(cls, news_list, regex_) -> list:
        for day in range(len(news_list)):
            for news in range(len(news_list[day])):
                news_list[day][news] = cls.clean_text(news_list[day][news], regex_)
        return news_list

    @classmethod
    def create_tone_dict(cls) -> dict:
        # os.chdir('ValueForecasting/Storage')
        tone_df = pd.read_csv('kartaslovsent.csv', sep=';')

        word_weight = []
        for i in range(len(tone_df)):
            if tone_df.tag[i] == 'NEUT':
                word_weight.append(0)
            if tone_df.tag[i] == 'NGTV':
                word_weight.append(-1)
            if tone_df.tag[i] == 'PSTV':
                word_weight.append(1)

        tone_df['weights'] = word_weight

        tone_df = tone_df.drop(['tag', 'value', 'pstv', 'ngtv', 'neut', 'dunno', 'pstvNgtvDisagreementRatio'], axis=1)

        return tone_df.set_index('term').T.to_dict('list')

    @classmethod
    def count_tone(cls, news_str, tone_dict):
        news = news_str.split()
        news_tone = 0
        for word in news:
            if word in tone_dict:
                news_tone += tone_dict[word][0]

        return news_tone / len(news) if len(news) != 0 else 0

    @classmethod
    def count_news_tone(cls, news_list, tone_dict):
        weights_list = []
        for day in range(len(news_list)):
            daily_news_list = []
            for news in range(len(news_list[day])):
                daily_news_list.append(cls.count_tone(news_list[day][news], tone_dict))

            weights_list.append(daily_news_list)
        return weights_list

    @classmethod
    def news_sort(cls, news_df):
        for i in range(len(news_df)):
            tup = zip(news_df.weights[i], news_df.news[i])

            sorted_tup = sorted(tup, key=lambda tpl: abs(tpl[0]), reverse=True)

            news_df.weights[i] = [val[0] for val in sorted_tup]
            news_df.news[i] = [val[1] for val in sorted_tup]

    @classmethod
    def slicer(cls, news_df, slice_size):
        for i in range(len(news_df)):
            news_df.news[i] = news_df.news[i][:slice_size]
            news_df.weights[i] = news_df.weights[i][:slice_size]

            while len(news_df.weights[i]) < slice_size:
                news_df.weights[i].append(0)

    @classmethod
    def run_preprocessing(cls, start_date: str, end_date: str):
        os.chdir(Path(os.path.dirname(__file__)).parent.joinpath('Storage'))
        print(os.path.join(os.path.dirname(__file__), os.pardir))
        news_df = Parser.parse_news(start_date, end_date)

        for i in range(len(news_df)):
            news_df.news[i] = cls.restrucurize(news_df.news[i])

        regex = re.compile("[А-Яа-яA-z]+")

        news_df.news = cls.cleaner(news_df.news, regex)

        tone_dict = cls.create_tone_dict()
        weights = cls.count_news_tone(news_df.news, tone_dict)
        news_df['weights'] = weights
        cls.news_sort(news_df)
        cls.slicer(news_df, 5)
        file_name = f'news_{start_date}_{end_date}_.json'

        news_df.to_json(file_name)

        return file_name #news_df

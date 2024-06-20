import datetime
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
from moexalgo import Ticker
from sklearn.preprocessing import MinMaxScaler


class DatasetPreprocessing:

    @classmethod
    def create_dataset(cls, dataset, look_back):
        dataX = []
        dataY = []
        for i in range(len(dataset) - look_back):
            a = dataset[i:(i + look_back)]
            dataX.append(a)
            dataY.append(dataset[i + look_back])
        return np.array(dataX), np.array(dataY)

    @classmethod
    def check_string(cls, s: str) -> bool:
        pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
        if pattern.match(s):
            return True
        else:
            return False

    @classmethod
    def check_datediff(cls, start_date: str, end_date: str) -> bool:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        datediff = (end_date - start_date).days
        if datediff >= 90:
            return True
        else:
            return False

    @classmethod
    def ticker_check(cls, ticker_name):
        try:
            ticker = Ticker(ticker_name)
        except Exception as e:
            return False, e
        else:
            return True, None

    @classmethod
    def data_gathering(cls, start_date: str, end_date: str, ticker_name: str):
        ticker = Ticker(ticker_name)
        data = ticker.candles(start=start_date, end=end_date, period='1d')
        data = data.rename(columns={'begin': 'date'})
        data.index = data['date'].values
        data = data[['close']]
        return data

    @classmethod
    def data_dataset(cls, data, split_range: int, look_back: int):
        data_copy = data.copy()

        data_copy.index = data_copy['date']
        data_copy = data_copy[['close']]

        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(data_copy.values.reshape(-1, 1))

        data_train = scaled_data[:-split_range].copy()
        data_test = scaled_data[-(split_range + look_back):].copy()

        data_train_x, data_train_y = cls.create_dataset(data_train, look_back)
        data_test_x, data_test_y = cls.create_dataset(data_test, look_back)

        data_train_x = np.reshape(data_train_x, (data_train_x.shape[0], 1, data_train_x.shape[1]))
        data_test_x = np.reshape(data_test_x, (data_test_x.shape[0], 1, data_test_x.shape[1]))

        return data_train_x, data_train_y, data_test_x, data_test_y, scaler, scaled_data

    @classmethod
    def news_dataset(cls, data, news, split_range: int, look_back: int):
        news_for_data = news[news['date'].isin(data.date)]
        news_weights = news_for_data[['weights']]
        news_weights.index = news_for_data['date']

        weights_array = np.array([np.array(val) for val in news_weights.weights])

        weights_train = weights_array[:-split_range].copy()
        weights_test = weights_array[-(split_range + look_back):].copy()

        weights_train_x, weights_train_y = cls.create_dataset(weights_train, look_back)
        weights_test_x, weights_test_y = cls.create_dataset(weights_test, look_back)

        weights_train_x = np.reshape(weights_train_x, (weights_train_x.shape[0], 5, weights_train_x.shape[1]))
        # 2й параметр 5 так как в функцию NewsPreprocessing.slicer передается параметр 5
        weights_test_x = np.reshape(weights_test_x, (weights_test_x.shape[0], 5, weights_test_x.shape[1]))

        return weights_train_x, weights_test_x

    @classmethod
    def dataset_generator(cls, news, start_date: str, end_date: str, look_back: int, ticker_name: str = 'SBER',
                          split_range: int = 7 * 4):

        data = cls.data_gathering(start_date, end_date, ticker_name)

        data_train_x, data_train_y, data_test_x, data_test_y, scaler, scaled_data = cls.data_dataset(data, split_range,
                                                                                                     look_back)

        # news = NewsPreprocessing.run_preprocessing(start_date, end_date)
        os.chdir(Path(os.path.dirname(__file__)).parent.joinpath('Storage', 'News data'))
        news_df = pd.read_json(news)
        weights_train_x, weights_test_x = cls.news_dataset(data, news_df, split_range, look_back)

        return data_train_x, data_train_y, data_test_x, data_test_y, \
            scaler, scaled_data, weights_train_x, weights_test_x

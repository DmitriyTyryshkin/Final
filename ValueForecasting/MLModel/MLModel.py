import os
from pathlib import Path

import keras as keras
import numpy as np
import pandas as pd
import tensorflow as tf
from keras import layers
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import chart_studio
import chart_studio.plotly as plotly
import plotly.graph_objs as go
from ValueForecasting.DatasetPreprocessing.DatasetPreprocessing import DatasetPreprocessing
from ValueForecasting.MLModel.schemas import Model


class MLModel:

    @classmethod
    def prepare_output(cls, model, data_train_x, data_test_x, scaler, scaled_data, weights_train_x, weights_test_x,
                       look_back):
        train_predict = scaler.inverse_transform(
            model.predict({'data_inputs': data_train_x, 'news_inputs': weights_train_x}))
        test_predict = scaler.inverse_transform(
            model.predict({'data_inputs': data_test_x, 'news_inputs': weights_test_x}))

        train_predict_plot = np.empty_like(scaled_data)
        train_predict_plot[:, :] = np.nan
        train_predict_plot[look_back:len(train_predict) + look_back, :] = train_predict

        test_predict_plot = np.empty_like(scaled_data)
        test_predict_plot[:, :] = np.nan
        test_predict_plot[-test_predict.shape[0]:len(scaled_data), :] = test_predict

        train_predict_df = pd.DataFrame(train_predict_plot, columns=['close'])
        # train_predict_df.drop(index=train_predict_df.index[0], axis= 0 , inplace= True )
        test_predict_df = pd.DataFrame(test_predict_plot, columns=['close'])
        # test_predict_df.drop(index=test_predict_df.index[0], axis= 0 , inplace= True )

        return train_predict, test_predict, train_predict_plot, test_predict_plot, train_predict_df, test_predict_df

    @classmethod
    def calculate_metrics(cls, scaler, test_y, test_predict):
        inverse_test_y = scaler.inverse_transform(test_y)
        mse = round(mean_squared_error(y_true=inverse_test_y, y_pred=test_predict), 5)
        mae = round(mean_absolute_error(y_true=inverse_test_y, y_pred=test_predict), 5)
        r2 = round(r2_score(y_true=inverse_test_y, y_pred=test_predict), 5)
        return mse, mae, r2

    @classmethod
    def plotting_forecast(cls, data, train_predict_df, test_predict_df):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['close'],
                                 mode='lines', name='actual'))
        fig.add_trace(go.Scatter(x=data.index, y=train_predict_df['close'].values,
                                 mode='lines', name='train predict'))
        fig.add_trace(go.Scatter(x=data.index, y=test_predict_df['close'].values,
                                 mode='lines', name='test predict'))

        # os.chdir('../../ValueForecastingServer/templates')
        os.chdir(Path(os.path.dirname(__file__)).parent.parent.joinpath('ValueForecastingServer', 'templates'))
        fig.write_html('forecast.html')

    @classmethod
    def new_model_forecast(cls, news, start_date: str, end_date: str, look_back: int = 2, ticker_name: str = 'SBER'):
        '''
        не доделано
        '''

        data_train_x, data_train_y, data_test_x, data_test_y, scaler, scaled_data, weights_train_x, weights_test_x = \
            DatasetPreprocessing.dataset_generator(news, start_date, end_date, look_back, ticker_name)

        data_inputs = keras.Input(shape=(1, look_back), name='data_inputs')
        data_branch = layers.LSTM(2 ** 7, activation="selu", return_sequences=True, name='data_branch_1')(data_inputs)
        data_branch = layers.LSTM(2 ** 7, activation="selu", name='data_branch_2')(data_branch)
        data_outputs = layers.Dropout(0.2)(data_branch)

        news_inputs = keras.Input(shape=(5, look_back), name='news_inputs')
        news_branch = layers.LSTM(2 ** 8, activation="selu", return_sequences=True, name='news_branch_1')(news_inputs)
        news_branch = layers.LSTM(2 ** 8, activation="selu", name='news_branch_2')(news_branch)
        news_outputs = layers.Dropout(0.2)(news_branch)

        merge = layers.concatenate([data_outputs, news_outputs], name='merge')
        data_news = layers.Dense((2 ** 7) + (2 ** 8), activation="selu", name='data_news')(merge)
        outputs = layers.Dense(1, activation='linear', name='data_news_outputs')(data_news)

        model = keras.Model(
            inputs=[data_inputs, news_inputs],
            outputs=[outputs],
        )

        model.compile(loss='mean_squared_error', optimizer='adam', metrics='R2Score')

        model.fit({'data_inputs': data_train_x, 'news_inputs': weights_train_x},
                  data_train_y,
                  epochs=20,
                  verbose=2)

        _, test_predict, _, _, train_predict_df, test_predict_df = cls.prepare_output(model, data_train_x,
                                                                                      data_test_x, scaler, scaled_data,
                                                                                      weights_train_x, weights_test_x,
                                                                                      look_back)

        data = DatasetPreprocessing.data_gathering(start_date, end_date, ticker_name)

        mse, mae, r2 = cls.calculate_metrics(scaler, data_test_y, test_predict)

        cls.plotting_forecast(data, train_predict_df, test_predict_df)

        Model.model = model
        Model.name = f"{ticker_name}_model_{r2}"
        Model.mse = mse
        Model.mae = mae
        Model.r2 = r2

        # return mse, mae, r2

    @classmethod
    def retrain_model(cls, news, start_date: str, end_date: str, look_back: int = 2, ticker_name: str = 'SBER'):

        data_train_x, data_train_y, data_test_x, data_test_y, scaler, scaled_data, weights_train_x, weights_test_x = \
            DatasetPreprocessing.dataset_generator(news, start_date, end_date, look_back, ticker_name)

        model = Model.model

        model.fit({'data_inputs': data_train_x, 'news_inputs': weights_train_x},
                  data_train_y,
                  epochs=20,
                  verbose=2)

        _, test_predict, _, _, train_predict_df, test_predict_df = cls.prepare_output(model, data_train_x,
                                                                                      data_test_x, scaler, scaled_data,
                                                                                      weights_train_x, weights_test_x,
                                                                                      look_back)

        data = DatasetPreprocessing.data_gathering(start_date, end_date, ticker_name)

        mse, mae, r2 = cls.calculate_metrics(scaler, data_test_y, test_predict)

        cls.plotting_forecast(data, train_predict_df, test_predict_df)

        Model.model = model
        Model.name = f"{ticker_name}_model_{r2}"
        Model.mse = mse
        Model.mae = mae
        Model.r2 = r2


    @classmethod
    def save_new_model(cls):
        os.chdir(Path(os.path.dirname(__file__)).parent.joinpath('Storage'))
        Model.model.save(Model.name)

    @classmethod
    def exist_model_forecast(cls, news, start_date: str, end_date: str, model_name: str = 'SBER_model_86.92',
                             look_back: int = 2, ticker_name: str = 'SBER'):
        os.chdir(Path(os.path.dirname(__file__)).parent.joinpath('Storage'))

        model = tf.keras.models.load_model(model_name)

        data_train_x, data_train_y, data_test_x, data_test_y, scaler, scaled_data, weights_train_x, weights_test_x = \
            DatasetPreprocessing.dataset_generator(news, start_date, end_date, look_back, ticker_name)

        _, test_predict, _, _, train_predict_df, test_predict_df = cls.prepare_output(model, data_train_x,
                                                                                      data_test_x, scaler, scaled_data,
                                                                                      weights_train_x, weights_test_x,
                                                                                      look_back)

        data = DatasetPreprocessing.data_gathering(start_date, end_date, ticker_name)

        mse, mae, r2 = cls.calculate_metrics(scaler, data_test_y, test_predict)

        cls.plotting_forecast(data, train_predict_df, test_predict_df)

        return mse, mae, r2

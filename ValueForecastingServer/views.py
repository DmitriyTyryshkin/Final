from ValueForecasting.DatasetPreprocessing.DatasetPreprocessing import DatasetPreprocessing
from ValueForecasting.MLModel.MLModel import MLModel
from ValueForecasting.NewsPreprocessing.NewsPreprocessing import NewsPreprocessing
from ValueForecastingServer.models import Models_list
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

from ValueForecastingServer.models import News_list
from django.views.decorators.csrf import csrf_exempt

from ValueForecasting.MLModel.schemas import Model


def home_page(request):
    models = Models_list.objects.all()
    news = News_list.objects.all()
    # for model in models:
    #     print(model.name)
    #     print(model.r2)
    return render(request, 'home_page.html', {'models_list': models, 'news_list': news})


def demo_forecast(request):
    if request.method == 'GET':
        return render(request, 'home_page.html', {'show_demo_forecast': True})


def new_model(request):
    news = News_list.objects.all()
    return render(request, 'create_model.html', {'news_list': news})


def create_new_model(request):
    if request.method == 'GET':
        ticker = request.GET.get('ticker_name')
        news_name = request.GET.get("select_interval")
        start_date = news_name.split('_')[1]
        end_date = news_name.split('_')[2]
        ticker_ok, ticker_e = DatasetPreprocessing.ticker_check(ticker)
        if ticker_ok:

            MLModel.new_model_forecast(start_date=start_date, end_date=end_date, ticker_name=ticker)
            return render(request, 'create_model.html', {'success': True, 'mse': Model.mse, 'mae': Model.mae,
                                                         'r2': Model.r2})
        else:
            return render(request, 'create_model.html', {'success': False, 'status': ticker_e})
            # HttpResponseBadRequest(request, content=ticker_e)


def retrain_model(request):
    pass


@csrf_exempt
def get_news(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if DatasetPreprocessing.check_string(start_date) and DatasetPreprocessing.check_string(end_date):
            # if DatasetPreprocessing.check_datediff(start_date, end_date):

                file_name = NewsPreprocessing.run_preprocessing(start_date, end_date)
                news_list = News_list()
                news_list.name = file_name
                news_list.start_date = start_date
                news_list.end_date = end_date
                news_list.save()
                return render(request, 'home_page.html', {'show_news_status': True, 'status': 'новости собраны'})

            # else:
            #     return render(request, 'home_page.html', {'show_news_status': True,
            #                                               'status': 'диапазон сбора данных меньше 90 дней'})

        else:
            return render(request, 'home_page.html', {'show_news_status': True, 'status': 'неправильный формат даты'})


def save_model(request):
    if request.method == 'POST':
        MLModel.save_new_model()
        return HttpResponseRedirect('/')


def select_model_and_news(request):
    if request.method == 'GET':
        model_name = request.GET.get("select_model")
        news_name = request.GET.get("select_interval")
        ticker = model_name.split('_')[0]
        start_date = news_name.split('_')[1]
        end_date = news_name.split('_')[2]
        mse, mae, r2 = MLModel.exist_model_forecast(news=news_name, start_date=start_date, end_date=end_date,
                                                    model_name=model_name, ticker_name=ticker)
        return render(request, 'home_page.html', {'show_forecast': True, 'mse': mse, 'mae': mae, 'r2': r2})

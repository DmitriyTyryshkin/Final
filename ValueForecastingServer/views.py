from ValueForecasting.DatasetPreprocessing.DatasetPreprocessing import DatasetPreprocessing
# from ValueForecasting.MLModel.MLModel import MLModel
from ValueForecasting.NewsPreprocessing.NewsPreprocessing import NewsPreprocessing
from ValueForecastingServer.models import Models_list
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render

from ValueForecastingServer.models import News_list
from django.views.decorators.csrf import csrf_exempt


def home_page(request):
    models = Models_list.objects.all()
    # for model in models:
    #     print(model.name)
    #     print(model.r2)
    return render(request, 'home_page.html', {'models_list': models})


def demo_forecast(request):
    if request.method == 'GET':
        return render(request, 'home_page.html', {'show_forecast': True})


def new_model(request):
    return render(request, 'create_model.html')


# def create_new_model(request):
#     if request.method == 'POST':
#         ticker = request.POST.get('ticker')
#         start_date = request.POST.get('start_date')
#         end_date = request.POST.get('end_date')
#         ticker_ok, ticker_e = DatasetPreprocessing.ticker_check(ticker)
#         if ticker_ok:
#             if DatasetPreprocessing.check_string(start_date) and DatasetPreprocessing.check_string(end_date):
#                 if DatasetPreprocessing.check_datediff(start_date, end_date):
#                     MLModel.new_model_forecast(start_date=start_date, end_date=end_date, ticker_name=ticker)
#                     return render(request, 'create_model.html', {'success': True, 'mse': Model.mse, 'mae': Model.mae,
#                                                                  'r2': Model.r2})
#                 else:
#                     return HttpResponseBadRequest(request, content='диапазон сбора данных меньше 90 дней')
#
#             else:
#                 return HttpResponseBadRequest(request, content='неправильный формат даты')
#
#         else:
#             return HttpResponseBadRequest(request, content=ticker_e)

@csrf_exempt
def get_news(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        if DatasetPreprocessing.check_string(start_date) and DatasetPreprocessing.check_string(end_date):
            # if DatasetPreprocessing.check_datediff(start_date, end_date): #отключено на время разработки
            file_name = NewsPreprocessing.run_preprocessing(start_date, end_date)
            news_list = News_list()
            news_list.name = file_name
            news_list.start_date = start_date
            news_list.end_date = end_date
            news_list.save()
            return render(request, 'home_page.html', {'show_news_status': True, 'status': 'новости собраны'})

        # else: #отключено на время разработки
        #     return render(request, 'home_page.html', {'show_news_status': True, 'status': 'диапазон сбора данных меньше 90 дней'})

        else:
            return render(request, 'home_page.html', {'show_news_status': True, 'status': 'неправильный формат даты'})


# def save_model(request):
#     if request.method == 'POST':
#         MLModel.save_new_model()
#         return HttpResponseRedirect('/')


def select_model(request):
    if request.method == 'GET':
        model_name = request.GET.get("select_model")
        news = News_list.objects.all()
        return render(request, 'model_forecasting.html', {'model_name': model_name, 'news_list': news})


def select_interval(request):
    if request.method == 'GET':
        model_name = request.POST.get("model_name")
        ticker = model_name.split('_')[0]
        news_name = request.GET.get("select_interval")
        start_date = news_name.split('_')[1]
        end_date = news_name.split('_')[2]
        mse, mae, r2 = MLModel.exist_model_forecast(news=news_name, start_date=start_date, end_date=end_date,
                                                    model_name=model_name, ticker_name=ticker)
        return render(request, 'model_forecasting.html', {'show_forecast': True, 'mse': mse, 'mae': mae, 'r2': r2})

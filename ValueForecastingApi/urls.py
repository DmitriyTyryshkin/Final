"""
URL configuration for ValueForecastingApi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from ValueForecastingServer import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.home_page),
    path("get_demo_forecast/", views.demo_forecast, name='demo_forecast'),
    path("new_model/", views.new_model, name='new_model'),
    path("get_news/", views.get_news, name='get_news'),
    # path("model_selection/", views.select_model, name='select_model'),
    path("select_model_and_news/", views.select_interval, name='select_model_and_news'),
]

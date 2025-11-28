from django.urls import path
from . import views

# Маршрути застосунку dashboard (підключені на кореневий рівень у config/urls.py)
urlpatterns = [
    path('', views.home, name='home'),              # головна сторінка
    path('statistics/', views.statistics, name='statistics'),  # статистика
    path('history/', views.history, name='history'),  # історія маршрутів/ставок
]


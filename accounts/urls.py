from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from . import views

# Кастомний logout: показує повідомлення після виходу
def logout_view(request):
    """Custom logout view with success message"""
    logout(request)
    messages.success(request, 'Ви успішно вийшли з акаунту.')
    return redirect('home')

# Маршрути застосунку accounts (у config/urls.py вже додано префікс accounts/)
urlpatterns = [
    path('login/', views.login_view, name='login'),              # сторінка входу
    path('logout/', logout_view, name='logout'),                 # вихід (кастомний)
    path('register/', views.register_view, name='register'),     # вибір типу реєстрації
    path('register/company/', views.register_company, name='register_company'),  # реєстрація компанії
    path('register/carrier/', views.register_carrier, name='register_carrier'), # реєстрація перевізника
    path('profile/', views.profile_view, name='profile'),        # профіль користувача
]


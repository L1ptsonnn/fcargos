from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from . import views

def logout_view(request):
    """Власний view для виходу з акаунту"""
    logout(request)
    messages.success(request, 'Ви успішно вийшли з акаунту.')
    return redirect('home')

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('register/company/', views.register_company, name='register_company'),
    path('register/carrier/', views.register_carrier, name='register_carrier'),
    path('profile/', views.profile_view, name='profile'),
]


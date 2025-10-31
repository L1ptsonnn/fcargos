from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register_view, name='register'),
    path('register/company/', views.register_company, name='register_company'),
    path('register/carrier/', views.register_carrier, name='register_carrier'),
    path('profile/', views.profile_view, name='profile'),
]


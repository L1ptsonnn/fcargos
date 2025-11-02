from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from . import views

# Custom logout view - adds success message after logout
def logout_view(request):
    """Custom logout view with success message"""
    logout(request)
    messages.success(request, 'Ви успішно вийшли з акаунту.')
    return redirect('home')

# URL patterns for accounts app
# All URLs here are prefixed with 'accounts/' (from config/urls.py)
urlpatterns = [
    path('login/', views.login_view, name='login'),              # Login page
    path('logout/', logout_view, name='logout'),                 # Logout (custom view)
    path('register/', views.register_view, name='register'),     # Registration type selection
    path('register/company/', views.register_company, name='register_company'),  # Company registration
    path('register/carrier/', views.register_carrier, name='register_carrier'), # Carrier registration
    path('profile/', views.profile_view, name='profile'),        # User profile page
]


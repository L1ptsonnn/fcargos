from django.urls import path
from . import views

# URL patterns for dashboard app
# These URLs are at root level (no prefix, from config/urls.py)
urlpatterns = [
    path('', views.home, name='home'),              # Home page (root URL)
    path('statistics/', views.statistics, name='statistics'),  # Statistics page
    path('history/', views.history, name='history'),  # Route/bid history page
]


from django.urls import path
from . import views

urlpatterns = [
    path('routes/', views.routes_list, name='routes_list'),
    path('routes/create/', views.create_route, name='create_route'),
    path('routes/<int:pk>/', views.route_detail, name='route_detail'),
    path('routes/<int:pk>/bid/', views.create_bid, name='create_bid'),
    path('routes/<int:pk>/complete/', views.complete_route, name='complete_route'),
    path('bids/<int:bid_id>/accept/', views.accept_bid, name='accept_bid'),
    path('tracking/<int:pk>/', views.tracking_view, name='tracking'),
    path('tracking/<int:pk>/update/', views.update_tracking, name='update_tracking'),
]


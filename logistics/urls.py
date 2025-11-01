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
    path('routes/<int:pk>/messages/', views.route_messages, name='route_messages'),
    path('routes/<int:pk>/messages/api/', views.route_messages_api, name='route_messages_api'),
    path('routes/<int:pk>/messages/send/', views.route_messages_send, name='route_messages_send'),
    path('chats/', views.chats_list, name='chats_list'),
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('api/chats/', views.chats_api, name='chats_api'),
    path('api/history/', views.history_api, name='history_api'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]


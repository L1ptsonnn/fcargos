from django.urls import path
from . import views

# Маршрути застосунку logistics
# У config/urls.py додано префікс logistics/
# <int:pk> — ID маршруту, <int:bid_id> — ID ставки
urlpatterns = [
    # Робота з маршрутами
    path('routes/', views.routes_list, name='routes_list'),                    # список маршрутів
    path('routes/create/', views.create_route, name='create_route'),           # створення маршруту
    path('routes/<int:pk>/', views.route_detail, name='route_detail'),          # деталі маршруту
    path('routes/<int:pk>/bid/', views.create_bid, name='create_bid'),         # створення ставки
    path('routes/<int:pk>/complete/', views.complete_route, name='complete_route'), # завершення маршруту
    
    # Ставки
    path('bids/<int:bid_id>/accept/', views.accept_bid, name='accept_bid'),    # прийняти ставку
    
    # Відстеження
    path('tracking/<int:pk>/', views.tracking_view, name='tracking'),          # сторінка трекінгу
    path('tracking/<int:pk>/update/', views.update_tracking, name='update_tracking'), # оновлення прогресу
    
    # Повідомлення/чат
    path('routes/<int:pk>/messages/', views.route_messages, name='route_messages'), # чат по маршруту
    path('routes/<int:pk>/messages/api/', views.route_messages_api, name='route_messages_api'), # Кінцева точка AJAX для чату
    path('routes/<int:pk>/messages/send/', views.route_messages_send, name='route_messages_send'), # відправлення повідомлень
    path('chats/', views.chats_list, name='chats_list'),                      # усі чати
    
    # Профілі користувачів
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),   # перегляд профілю
    
    # Ендпоїнти AJAX
    path('api/notifications/', views.notifications_api, name='notifications_api'), # отримати сповіщення
    path('api/chats/', views.chats_api, name='chats_api'),                    # список чатів
    path('api/history/', views.history_api, name='history_api'),              # історія
    
    # Управління сповіщеннями
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'), # позначити як прочитане
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),   # позначити всі як прочитані
]


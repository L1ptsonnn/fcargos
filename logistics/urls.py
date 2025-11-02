from django.urls import path
from . import views

# URL patterns for logistics app
# All URLs here are prefixed with 'logistics/' (from config/urls.py)
# <int:pk> means URL parameter (route ID), <int:bid_id> means bid ID
urlpatterns = [
    # Route management
    path('routes/', views.routes_list, name='routes_list'),                    # List of all routes
    path('routes/create/', views.create_route, name='create_route'),           # Create new route
    path('routes/<int:pk>/', views.route_detail, name='route_detail'),          # Route details page
    path('routes/<int:pk>/bid/', views.create_bid, name='create_bid'),         # Create bid on route
    path('routes/<int:pk>/complete/', views.complete_route, name='complete_route'), # Mark route as delivered
    
    # Bid management
    path('bids/<int:bid_id>/accept/', views.accept_bid, name='accept_bid'),    # Accept a bid
    
    # Tracking
    path('tracking/<int:pk>/', views.tracking_view, name='tracking'),          # Route tracking page
    path('tracking/<int:pk>/update/', views.update_tracking, name='update_tracking'), # Update tracking progress
    
    # Messages/Chat
    path('routes/<int:pk>/messages/', views.route_messages, name='route_messages'), # Messages page for route
    path('routes/<int:pk>/messages/api/', views.route_messages_api, name='route_messages_api'), # AJAX API for messages
    path('routes/<int:pk>/messages/send/', views.route_messages_send, name='route_messages_send'), # Send message
    path('chats/', views.chats_list, name='chats_list'),                      # List of all chats
    
    # User profiles
    path('profile/<int:user_id>/', views.user_profile, name='user_profile'),   # View any user's profile
    
    # AJAX API endpoints
    path('api/notifications/', views.notifications_api, name='notifications_api'), # Get notifications (AJAX)
    path('api/chats/', views.chats_api, name='chats_api'),                    # Get chats list (AJAX)
    path('api/history/', views.history_api, name='history_api'),              # Get history (AJAX)
    
    # Notification management
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'), # Mark notification as read
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),   # Mark all notifications as read
]


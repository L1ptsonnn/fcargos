from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Admin site configuration
# Customize Django admin panel header and titles
admin.site.site_header = 'FCargos Адмін-панель'
admin.site.site_title = 'FCargos'
admin.site.index_title = 'Управління системою'

# Main URL patterns for the project
# Each path maps a URL to a view or includes URLs from another app
urlpatterns = [
    path('admin/', admin.site.urls),              # Django admin panel
    path('', include('dashboard.urls')),          # Home page, statistics, history
    path('accounts/', include('accounts.urls')),  # Login, registration, profiles
    path('logistics/', include('logistics.urls')), # Routes, bids, tracking, chats
]

# Serve media files in development mode (only when DEBUG=True)
# In production, serve these files through web server (nginx, Apache)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

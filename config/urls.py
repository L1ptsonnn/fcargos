from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Налаштування адмін-панелі (тексти, заголовки)
admin.site.site_header = 'FCargos Адмін-панель'
admin.site.site_title = 'FCargos'
admin.site.index_title = 'Управління системою'

# Основні маршрути проєкту
# Кожен path веде на view або включає urls іншого застосунку
urlpatterns = [
    path('admin/', admin.site.urls),              # адмін-панель Django
    path('', include('dashboard.urls')),          # головна, статистика, історія
    path('accounts/', include('accounts.urls')),  # логін, реєстрація, профілі
    path('logistics/', include('logistics.urls')), # маршрути, ставки, чати
]

# Статика та медіа під час розробки (DEBUG=True)
# У продакшні ці файли має віддавати вебсервер (nginx/Apache)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

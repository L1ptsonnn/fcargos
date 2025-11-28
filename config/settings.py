"""
Налаштування Django-проєкту FCargos.
Тут визначаємо підключені застосунки, базу даних PostgreSQL,
шляхи до статичних/медійних файлів і базові параметри безпеки.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Шляхи визначаємо як BASE_DIR / 'subdir'.
# Змінна BASE_DIR — корінь проєкту
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

# Налаштування для розробки; перед продакшном обов'язково пройти чекліст
# Докладніше: https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# УВАГА: секретний ключ у продакшні має бути прихованим
# Використовується для підписів — не поширюємо!
SECRET_KEY = 'django-insecure-pmeube#7m+19!8(gh2xd)o(0hn+@q-%tdtg^hu@g77rt-dx&*o'

# Параметр DEBUG=True лише для розробки (показує детальні помилки)
# У продакшні вимикаємо
DEBUG = True

# Поле ALLOWED_HOSTS містить список дозволених доменів
# Порожній список означає «всі» (лише локально)
ALLOWED_HOSTS = []


# Налаштування застосунків
# Список INSTALLED_APPS містить усі увімкнені Django-додатки
INSTALLED_APPS = [
    # Вбудовані Django-додатки
    'django.contrib.admin',          # Адмін-панель
    'django.contrib.auth',           # Автентифікація
    'django.contrib.contenttypes',   # Типи контенту
    'django.contrib.sessions',       # Сесії
    'django.contrib.messages',       # Повідомлення
    'django.contrib.staticfiles',   # Статика
    
    # Сторонні пакети
    'crispy_forms',                  # Зручні форми
    'crispy_bootstrap5',             # Тема Bootstrap 5
    
    # Наші застосунки
    'accounts',                       # Акаунти, реєстрація, профілі
    'logistics',                     # Маршрути, ставки, трекінг, повідомлення
    'dashboard',                     # Головна, статистика, історія
]

# Перелік MIDDLEWARE описує проміжні обробники запитів/відповідей
# Порядок важливий (проходження вниз на запиті й вгору на відповіді)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',           # Безпека і заголовки
    'django.contrib.sessions.middleware.SessionMiddleware',   # Сесії
    'django.middleware.common.CommonMiddleware',               # Базові HTTP-утиліти
    'django.middleware.csrf.CsrfViewMiddleware',              # захист від CSRF
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Авторизація
    'django.contrib.messages.middleware.MessageMiddleware',   # Повідомлення
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Захист від clickjacking
]

# Параметр ROOT_URLCONF вказує на головний файл маршрутів
# Тут підключаємо URL-и застосунків
ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Налаштування бази даних
# Докладніше: https://docs.djangoproject.com/en/5.2/ref/settings/#databases
# Параметри PostgreSQL беремо зі змінних середовища
# За замовчуванням використовуємо SQLite, щоб проект запускався без додаткових сервісів

USE_POSTGRES = os.getenv('USE_POSTGRES', 'false').lower() in ('1', 'true', 'yes')

if USE_POSTGRES:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'fcargos'),
            'USER': os.getenv('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'postgres'),
            'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Валідатори паролів
# Докладніше: https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Інтернаціоналізація
# Докладніше: https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Kyiv'

USE_I18N = True

USE_TZ = True


# Статичні файли (CSS, JavaScript, зображення)
# Докладніше: https://docs.djangoproject.com/en/5.2/howto/static-files/

# Префікс URL для статики
STATIC_URL = 'static/'
# Тека зі статикою в режимі розробки
STATICFILES_DIRS = [BASE_DIR / 'static']
# Куди collectstatic збирає файли для продакшну
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Медіафайли (логотипи та інші завантаження)
# Префікс URL для медіа
MEDIA_URL = 'media/'
# Директорія збереження медіа
MEDIA_ROOT = BASE_DIR / 'media'

# Налаштування Crispy Forms (Bootstrap 5)
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Кастомна модель користувача, яку використовує Django
AUTH_USER_MODEL = 'accounts.User'

# Тип primary key за замовчуванням
# Докладніше: https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Мова та часовий пояс
LANGUAGE_CODE = 'uk'

# Посилання для аутентифікації
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

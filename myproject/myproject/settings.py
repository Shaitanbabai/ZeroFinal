import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ValidationError
import re
import allauth

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Загрузите переменные из .env файла
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False') == 'True'
# DEBUG = False

ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    # Добавьте необходимые social providers, если используются
    # 'allauth.socialaccount',
    # 'allauth.socialaccount.providers.google',
    # 'allauth.socialaccount.providers.facebook',
    'bootstrap4',
    # 'templatetags.form_tags'
    'business_app',
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [

           'django.contrib.auth.backends.ModelBackend',
           'allauth.account.auth_backends.AuthenticationBackend',

]

# Конфигурации allauth
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_PASSWORD_MIN_LENGTH = 10
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_RATE_LIMITS = {
    'login_failed': '5/60s'  # 5 неудачных попыток за 60 секунд
}

# Укажите кастомные формы
ACCOUNT_FORMS = {
    'signup': 'business_app.forms.CustomSignupForm',
    'login': 'business_app.forms.CustomLoginForm',
}

# Переадресации
LOGIN_REDIRECT_URL = 'main_page'  # Обновите в зависимости от вашей главной страницы
LOGOUT_REDIRECT_URL = 'login'  # URL, на который перенаправляется пользователь после выхода

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

"""Настройки для отправки электронных писем в Django с использованием django-allauth.

Эти настройки позволяют отправлять письма на реальные электронные адреса, для функционала подтверждения email, 
восстановления пароля и других операций в django-allauth.

Шаги по настройке:
1. Выбрать подходящий бэкенд для отправки писем.
2. Настроить параметры SMTP-сервера.
3. Убедиться, что настройки безопасности учтены.
4. Проверить и протестировать отправку писем.


# Выбрать подходящий бэкенд для отправки писем.
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Настроить параметры SMTP-сервера.
# EMAIL_HOST = 'smtp.example.com'
# EMAIL_PORT = 587
# EMAIL_HOST_USER = 'your-email@example.com'
# EMAIL_HOST_PASSWORD = 'your-email-password'
# EMAIL_USE_TLS = True

# Настройки для отправки электронных писем в Django с использованием django-allauth.
Убедиться, что настройки безопасности учтены.
Если вы используете сервисы вроде Gmail, убедитесь, что включена поддержка безопасных приложений 
или используйте специальные пароли для приложений.

Проверить и протестировать отправку писем.
Убедитесь, что письма отправляются корректно, протестировав функционал через интерфейс django-allauth
# (например, регистрация пользователя и подтверждение email).
"""

# Для разработки, меняйте на SMTP в продакшене
DEFAULT_FROM_EMAIL = 'webmaster@localhost'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'business_app', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'business_app.context_processors.user_group_context',
            ],
        },
    },
]

# Дополнительные настройки, если используете социальную аутентификацию
# SOCIALACCOUNT_PROVIDERS = {
#     'google': {
#         'SCOPE': [
#             'profile',
#             'email',
#         ],
#         'AUTH_PARAMS': {
#             'access_type': 'online',
#         },
#     }
# }

WSGI_APPLICATION = 'myproject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Использование базы данных для хранения сессий
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True  # Установите True, если используете HTTPS
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 7200  # Установите время жизни сессии в секундах


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

class MinimumNumberValidator:
    def __init__(self, min_numbers=1):
        self.min_numbers = min_numbers

    def validate(self, password, user=None):  # noqa: ARG002
        if len(re.findall(r'\d', password)) < self.min_numbers:
            raise ValidationError(
                f'This password must contain at least {self.min_numbers} digit(s).',
                code='password_no_number',
            )

    def get_help_text(self):
        return f'Your password must contain at least {self.min_numbers} digit(s).'


class MinimumUppercaseValidator:
    def __init__(self, min_uppercase=1):
        self.min_uppercase = min_uppercase

    def validate(self, password, user=None):  # noqa: ARG002
        if len(re.findall(r'[A-Z]', password)) < self.min_uppercase:
            raise ValidationError(
                f'This password must contain at least {self.min_uppercase} uppercase letter(s).',
                code='password_no_uppercase',
            )

    def get_help_text(self):
        return f'Your password must contain at least {self.min_uppercase} uppercase letter(s).'


class MinimumLowercaseValidator:
    def __init__(self, min_lowercase=1):
        self.min_lowercase = min_lowercase

    def validate(self, password, user=None):  # noqa: ARG002
        if len(re.findall(r'[a-z]', password)) < self.min_lowercase:
            raise ValidationError(
                f'This password must contain at least {self.min_lowercase} lowercase letter(s).',
                code='password_no_lowercase',
            )

    def get_help_text(self):
        return f'Your password must contain at least {self.min_lowercase} lowercase letter(s).'


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'myproject.settings.MinimumNumberValidator',
        'OPTIONS': {
            'min_numbers': 1,
        }
    },
    {
        'NAME': 'myproject.settings.MinimumUppercaseValidator',
        'OPTIONS': {
            'min_uppercase': 1,
        }
    },
    {
        'NAME': 'myproject.settings.MinimumLowercaseValidator',
        'OPTIONS': {
            'min_lowercase': 1,
        }
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'

# STATICFILES_DIRS указывает на дополнительные директории, где искать статические файлы.
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'business_app', 'static'),  # Путь к статическим файлам приложения
]

# STATIC_ROOT — это директория, куда будут собираться все статические файлы после выполнения команды collectstatic.
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Настройки для медиа-файлов
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

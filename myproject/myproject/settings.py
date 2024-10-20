import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ValidationError
import re

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Загрузите переменные из .env файла
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = []


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
    'allauth.socialaccount',
# Добавьте необходимые social providers, если используются
# 'allauth.socialaccount.providers.google',
# 'allauth.socialaccount.providers.facebook',
    'business_app',
]

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
       'django.contrib.auth.backends.ModelBackend',
       'allauth.account.auth_backends.AuthenticationBackend',
]

# Конфигурации allauth
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_PASSWORD_MIN_LENGTH = 10
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_RATE_LIMITS = {
    'login_failed': '5/60s'  # 5 неудачных попыток за 60 секунд
}
LOGIN_REDIRECT_URL = '/custom-redirect/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'  # URL, на который перенаправляется пользователь после выхода

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

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
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myproject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


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

STATIC_DIRS = [
    BASE_DIR/'static',
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

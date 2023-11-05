"""
Django settings for PilotTest project.

Generated by 'django-admin startproject' using Django 4.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
from loggers.my_loggers import TelegramMsgLog
from pathlib import Path
from decouple import config  # позволяет скрывать критическую информацию (пароли, логины, ip)
# from quize737.common import DKIMBackend

import common
import os
import logging

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
secret_key = config('secret_key', default='')
SECRET_KEY = secret_key

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "common": {
            "format": '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
            "datefmt": "%d:%m:%Y %H:%M:%S"
        },
        "answers": {
            "format": '%(asctime)s %(name)-12s %(message)s',
            "datefmt": "%d:%m:%Y %H:%M:%S"
        },

    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
        "file_answers": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR / "log/answers.log"),
            'formatter': 'answers'},

        "file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR / "log/pilottest.log"),
            'formatter': 'common'},

        "bot": {
            "level": "WARNING",
            "class": "loggers.my_loggers.TelegramMsgLog"
        }
    },

    "loggers": {
        "root": {
            "handlers": ["file", "console"],
            "level": "WARNING",
            "propagate": False
        },
        "USER ACTION": {  # Критические действия пользователей (удаление тестов, вопросов...)
            "handlers": ["file", "bot"],
            "level": "WARNING",
            "propagate": True,
        },
        "PILOT ANSWER": {  # Ответы тестируемых
            "handlers": ["file_answers"],
            "level": "INFO",
            "propagate": True,
        },
        "django.server": {
            "handlers": ["bot"],
            "level": "ERROR",
            "propagate": True
        },
    },
}

EMAIL_HOST = config('EMAIL_HOST', default='')
EMAIL_PORT = config('EMAIL_PORT', default='')
EMAIL_USE_TLS = True
# EMAIL_USE_SSL = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('SENDER_MAIL', default='')

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

ALLOWED_HOSTS = ['*']

# Application definition

# DATETIME_FORMAT = ['%d %M %Y']
# DATE_INPUT_FORMATS = ['%d %M %Y']
DATE_FORMAT = ['%d %M %Y']

INSTALLED_APPS = [
    'django_htmx',
    'django_cron',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_template_maths',
    'users',
    'quize737',
    'PilotLoad',
    'DBLoad'
]

MIDDLEWARE = [
    'django_htmx.middleware.HtmxMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'PilotTest.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates/')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'builtins': [
                'quize737.templatetags.tags',
            ]
        },
    },
]

WSGI_APPLICATION = 'PilotTest.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

db_adress = config('ip_mysql', default='')
db_name = config('SQL_DB', default='')
db_user = config('SQL_usrID', default='')
db_pass = config('SQL_password', default='')
db_port = config('db_port', default='')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': db_name,
        'USER': db_user,
        'PASSWORD': db_pass,
        'HOST': db_adress,
        'PORT': db_port,
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 3}
    },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# STATIC_ROOT = os.getcwd() + '/static/'
STATIC_ROOT = os.path.join(BASE_DIR / 'static/')

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# STATICFILES_DIRS = [
#       'C:/Users/User/PycharmProjects/PilotTest/'
#  ]

LOGIN_REDIRECT_URL = 'start'
LOGIN_URL = 'login'

CRON_CLASSES = [
    "quize737.cron.MyCronJob",
]

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
}

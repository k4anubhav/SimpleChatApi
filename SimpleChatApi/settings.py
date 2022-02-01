import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv, set_key

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    set_key(str(BASE_DIR / '.env'), 'SECRET_KEY', get_random_secret_key())
    load_dotenv()

ALLOWED_HOSTS = []

DEBUG = (True if _x.lower() == 'true' else False) if (_x := os.environ.get('DEBUG')) else False
if not DEBUG:
    set_key(str(BASE_DIR / '.env'), 'DEBUG', 'False')
    ALLOWED_HOSTS.append('127.0.0.1')

USE_IPB = (True if _x.lower() == 'true' else False) if (_x := os.environ.get('USE_IPB')) else False

print(f'DEBUG: {DEBUG}')
print(f'USE_IPB: {USE_IPB}')

# Application definition

INSTALLED_APPS = [
    'channels',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',

    'user',
    'core',
    'api',
    'websocket',

    'drf_spectacular',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'user.authentication.TokenAuthentication',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'SimpleChat API',
    'DESCRIPTION': 'A open source chat api',
    'VERSION': '1.0.0',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'SimpleChatApi.middleware.CsrfExemptSessionAuthenticationMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # 'user.middleware.TokenMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'SimpleChatApi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'SimpleChatApi.wsgi.application'
ASGI_APPLICATION = 'SimpleChatApi.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
        # 'BACKEND': 'channels_redis.core.RedisChannelLayer',
        # 'CONFIG': {
        #     "hosts": [('127.0.0.1', 6379)],
        # },
    },
}

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASE_ROUTERS = ('user.dbrouters.MyDBRouter', 'core.dbrouters.MyDBRouter')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# IPB uses mariaDB as per my knowledge
if USE_IPB:
    DATABASES.update({
        'chats': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('IPB_DATABASE_NAME'),
            'USER': os.environ.get('IPB_DATABASE_USER'),
            'PASSWORD': os.environ.get('IPB_DATABASE_PASSWORD'),
            'HOST': os.environ.get('IPB_DATABASE_HOST'),
            'PORT': '',
        }
    })

AUTH_USER_MODEL = 'user.User'

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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

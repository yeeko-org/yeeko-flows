import os

from dotenv import load_dotenv
from pathlib import Path

from config.utils import getenv_bool, getenv_list

load_dotenv()


ADMINS = (('Yeeko Report', 'ricardo@yeeko.org'), )
APP_VERSION = os.getenv('APP_VERSION', '5.0.0')
BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = getenv_bool('DEBUG')
D_PPRINT = getenv_bool('D_PPRINT', False)


# Django base config
ALLOWED_HOSTS = getenv_list('ALLOWED_HOSTS', ['*'])

SECRET_KEY = os.getenv(
    'SECRET_KEY', 'yeeko-django-insecure-*#v9ug2&ua-98ubs7u7)!uvqn*ud#ct73oh5'
)

AUTH_USER_MODEL = os.getenv('AUTH_USER_MODEL', 'auth.User')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


APPEND_SLASH = getenv_bool('APPEND_SLASH', False)
DATETIME_INPUT_FORMATS = ('%Y-%m-%d %H:%M:%S',)
HTTP_X_FORWARDED_HOST = os.getenv('HTTP_X_FORWARDED_HOST')
USE_X_FORWARDED_HOST = getenv_bool('USE_X_FORWARDED_HOST')

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'


INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'infrastructure.users.apps.UsersConfig',
    'infrastructure.service.apps.ServiceConfig',
    'infrastructure.place.apps.PlaceConfig',
    'infrastructure.member.apps.MemberConfig',
    'infrastructure.flow.apps.FlowConfig',
    'infrastructure.xtra.apps.XtraConfig',
    'infrastructure.tool.apps.ToolConfig',
    'infrastructure.box.apps.BoxConfig',
    'infrastructure.assign.apps.AssingConfig',
    'infrastructure.talk.apps.TalkConfig',
)


# ----------------------------Internationalization----------------------------
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'es-us')
TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')
USE_I18N = getenv_bool('USE_I18N')
USE_L10N = getenv_bool('USE_L10N')
USE_TZ = getenv_bool('USE_TZ')
# ---------------------------/Internationalization----------------------------


# ----------------------------------Data Base---------------------------------
POSTRGRESQL_DB = getenv_bool('POSTRGRESQL_DB', False)
DATABASE_NAME = os.getenv('DATABASE_NAME', 'db.sqlite3')

if POSTRGRESQL_DB:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': DATABASE_NAME,
            'USER': os.getenv('DATABASE_USER'),
            'PASSWORD': os.getenv('DATABASE_PASSWORD'),
            'HOST': os.getenv('DATABASE_HOST'),
            'PORT': 5432,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / DATABASE_NAME
        }
    }
# ---------------------------------/Data Base---------------------------------


# ----------------------Template, statics, media, storage---------------------
STATIC_PATH = BASE_DIR / 'static'

STATICFILES_DIRS = (STATIC_PATH, BASE_DIR / '../dist/prod')

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

COMPRESS_URL = os.getenv('COMPRESS_URL', '/static/')
COMPRESS_ROOT = BASE_DIR / 'static_compressed'
COMPRESS_ENABLED = getenv_bool('COMPRESS_ENABLED')
COMPRESS_OFFLINE = getenv_bool('COMPRESS_OFFLINE')

STATIC_URL = COMPRESS_URL
STATIC_ROOT = COMPRESS_ROOT

MEDIA_PATH = BASE_DIR / 'media'
MEDIA_ROOT = MEDIA_PATH
MEDIA_URL = os.getenv('MEDIA_URL', '/media/')

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

# ---------------------/Template, statics, media, storage---------------------


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)


# ------------------------------------CSRF------------------------------------

CSRF_TRUSTED_ORIGINS = getenv_list('CSRF_TRUSTED_ORIGINS', [])
CORS_ORIGIN_ALLOW_ALL = getenv_bool('CORS_ORIGIN_ALLOW_ALL')
CORS_ALLOWED_ORIGINS = getenv_list('CORS_ALLOWED_ORIGINS', [])
CORS_ORIGIN_WHITELIST = getenv_list('CORS_ORIGIN_WHITELIST', [])

CORS_ALLOW_HEADERS = (
    'x-requested-with',
    'Content-type',
    'HTTP_HOST',
    'accept',
    'origin',
)
CORS_ALLOW_CREDENTIALS = getenv_bool('CORS_ALLOW_CREDENTIALS')

DOMAINS_ALLOWED = getenv_list('DOMAINS_ALLOWED', [])

# -----------------------------------/CSRF------------------------------------

# ---------------------------DJANGO REST FRAMEWORK----------------------------
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'config.settings.authentication.BearerAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    )
}
# ---------------------------DJANGO REST FRAMEWORK----------------------------

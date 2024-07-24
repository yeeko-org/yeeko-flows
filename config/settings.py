import os
from os import getenv
from dotenv import load_dotenv
from pathlib import Path

from config.utils import getenv_bool, getenv_db, getenv_list, getenv_int

load_dotenv()


ADMINS = (('Yeeko Report', 'ricardo@yeeko.org'), )
APP_VERSION = getenv('APP_VERSION', '5.0.0')
BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = getenv_bool('DEBUG')
SITE_ID = getenv_int('SITE_ID', 1)


# Django base config
ALLOWED_HOSTS = getenv_list('ALLOWED_HOSTS', ['*'])

SECRET_KEY = getenv(
    'SECRET_KEY', 'yeeko-django-insecure-secret-key'
)

AUTH_USER_MODEL = getenv('AUTH_USER_MODEL', 'auth.User')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


APPEND_SLASH = getenv_bool('APPEND_SLASH', False)
DATETIME_INPUT_FORMATS = ('%d-%m-%Y %H:%M:%S',)
HTTP_X_FORWARDED_HOST = getenv('HTTP_X_FORWARDED_HOST', False)
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
    'storages',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'infrastructure.users.apps.UsersConfig',
    'infrastructure.service.apps.ServiceConfig',
    'infrastructure.place.apps.PlaceConfig',
    'infrastructure.persistent_media.apps.PersistentMediaConfig',
    'infrastructure.member.apps.MemberConfig',
    'infrastructure.flow.apps.FlowConfig',
    'infrastructure.xtra.apps.XtraConfig',
    'infrastructure.tool.apps.ToolConfig',
    'infrastructure.box.apps.BoxConfig',
    'infrastructure.assign.apps.AssingConfig',
    'infrastructure.talk.apps.TalkConfig',
    'presentation',
)


# ----------------------------Internationalization----------------------------
LANGUAGE_CODE = getenv('LANGUAGE_CODE', 'es-us')
TIME_ZONE = getenv('TIME_ZONE', 'UTC')
USE_I18N = getenv_bool('USE_I18N')
USE_L10N = getenv_bool('USE_L10N')
USE_TZ = getenv_bool('USE_TZ')
# ---------------------------/Internationalization----------------------------


# ----------------------------------Data Base---------------------------------
POSTRGRESQL_DB = getenv_bool('POSTRGRESQL_DB', False)

DATABASES = {
    'default': getenv_db(is_postgres=POSTRGRESQL_DB)
}
# ---------------------------------/Data Base---------------------------------


# ----------------------Template, statics, media, storage---------------------
STATIC_PATH = BASE_DIR / 'static'

STATICFILES_DIRS = (STATIC_PATH, BASE_DIR / '../dist/prod')

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

COMPRESS_URL = getenv('COMPRESS_URL', '/static/')
COMPRESS_ROOT = BASE_DIR / 'static_compressed'
COMPRESS_ENABLED = getenv_bool('COMPRESS_ENABLED')
COMPRESS_OFFLINE = getenv_bool('COMPRESS_OFFLINE')

STATIC_URL = COMPRESS_URL
STATIC_ROOT = COMPRESS_ROOT


S3_STORAGE_MANAGER = getenv_bool('S3_STORAGE_MANAGER', True)

if S3_STORAGE_MANAGER:

    AWS_ACCESS_KEY_ID = getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = getenv('AWS_SECRET_ACCESS_KEY')

    AWS_STORAGE_BUCKET_NAME = getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = getenv('AWS_S3_REGION_NAME')
    AWS_PRELOAD_METADATA = getenv_bool('AWS_PRELOAD_METADATA', True)
    AWS_S3_CUSTOM_DOMAIN = getenv('AWS_S3_CUSTOM_DOMAIN')

    # AWS_LOCATION = 'media'
    AWS_DEFAULT_ACL = getenv('AWS_DEFAULT_ACL', 'public-read')

    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    AWS_MEDIA_URL = getenv('AWS_MEDIA_URL', '')
    MEDIA_URL = AWS_MEDIA_URL + "/"

    AWS_S3_FILE_OVERWRITE = getenv_bool('AWS_S3_FILE_OVERWRITE', False)

    CAN_DELETE_AWS_STORAGE_FILES = getenv_bool(
        'CAN_DELETE_AWS_STORAGE_FILES', False)

else:

    MEDIA_PATH = BASE_DIR / 'media'
    MEDIA_ROOT = MEDIA_PATH
    MEDIA_URL = getenv('MEDIA_URL', '/media/')

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
        'NAME': 'django.contrib.auth.password_validation.'
        'UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'CommonPasswordValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


MIDDLEWARE = (
    'config.local_host_middleware.LocalhostMiddleware',
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


# -----------------------------------Meta-------------------------------------
WEBHOOK_TOKEN_WHATSAPP = getenv('WEBHOOK_TOKEN_WHATSAPP', 'whatsapp')
# -----------------------------------Meta-------------------------------------

CREATE_USER_PRIVATE_HASH = getenv('CREATE_USER_PRIVATE_HASH', 'yeeko')

# ---------------------------DJANGO REST FRAMEWORK----------------------------

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    )
}

# -------------------------end DJANGO REST FRAMEWORK--------------------------

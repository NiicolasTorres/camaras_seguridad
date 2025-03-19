
from pathlib import Path
import os
import firebase_admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from firebase_admin import credentials, initialize_app


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-ohkd*@hy#$&id&aah)l-zjteu^xtvb(s0u)_db=&3uo%@yc@9!'

DEBUG = True

ALLOWED_HOSTS = []

LOGIN_REDIRECT_URL = '/profile/'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'reconocimiento',
    'cuentas',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'camaras.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  
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


WSGI_APPLICATION = 'camaras.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'security_db',
        'USER': 'postgres',
        'PASSWORD': '300840',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'client_encoding': 'UTF8',
        },
    }
}


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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Obtener la ruta base del proyecto
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ruta correcta para firebase_credentials.json
cred_path = os.path.join(base_dir, 'firebase_credentials.json')

# Verificar que el archivo existe antes de intentar inicializar
if os.path.exists(cred_path):
    # Inicializar la aplicación de Firebase
    cred = credentials.Certificate(cred_path)
    initialize_app(cred)
else:
    print(f"Error: El archivo {cred_path} no existe.")
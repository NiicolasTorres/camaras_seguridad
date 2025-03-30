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


#Email de admins

ADMINS = [
    ('Federico Torres', 'federico.-torres@hotmail.com'),
]

#email

# Configuración para enviar correos electrónicos en Django (ejemplo usando Gmail)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # O el host de tu servidor SMTP
EMAIL_PORT = 587  # Puerto para TLS
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'thesiriuscat1@gmail.com'  # Tu correo electrónico de Gmail
EMAIL_HOST_PASSWORD = '987/987_asd'  # La contraseña de tu cuenta de correo (o aplicación)

# Vapid

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VAPID_PRIVATE_KEY = os.path.join(BASE_DIR, 'vapid_private.pem')
VAPID_PUBLIC_KEY = os.path.join(BASE_DIR, 'vapid_public.pem')
VAPID_CLAIMS = {
    "sub": "mailto:federico.-torres@hotmail.com"  
}
print(os.path.exists(VAPID_PRIVATE_KEY), os.path.exists(VAPID_PUBLIC_KEY))

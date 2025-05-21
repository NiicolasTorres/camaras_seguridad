from pathlib import Path
import os
from django.contrib.staticfiles.urls import staticfiles_urlpatterns



BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-ohkd*@hy#$&id&aah)l-zjteu^xtvb(s0u)_db=&3uo%@yc@9!'

DEBUG = False

ALLOWED_HOSTS = ['app.silenteye.com.mx', '75.119.148.43', 'localhost']

CSRF_TRUSTED_ORIGINS = [
    'https://app.silenteye.com.mx',
]

LOGIN_REDIRECT_URL = '/profile/'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'reconocimiento',
    'cuentas',
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', 
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'OPTIONS',
]

CORS_ALLOWED_ORIGINS = [
    'https://app.silenteye.com.mx',
    'https://ad66-2a02-c207-2254-5754-00-1.ngrok-free.app',
]
CSRF_TRUSTED_ORIGINS = [
    'https://app.silenteye.com.mx',
    'https://ad66-2a02-c207-2254-5754-00-1.ngrok-free.app',
]


CORS_ALLOW_HEADERS = [
    'content-type',
    'accept',
    'x-requested-with',
    'authorization', 
]


CSRF_TRUSTED_ORIGINS = [
    'https://app.silenteye.com.mx',
    'https://ad66-2a02-c207-2254-5754-00-1.ngrok-free.app',
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

LANGUAGE_CODE = 'es' 

TIME_ZONE = 'America/Mexico_City'


USE_I18N = True
USE_L10N = True

USE_TZ = True


STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


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
EMAIL_HOST_USER = ''  # Correo electrónico de Gmail
EMAIL_HOST_PASSWORD = ''  # La contraseña del cuenta de correo 

# Vapid


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VAPID_PRIVATE_KEY = os.path.join(BASE_DIR, 'vapid_private.pem')
VAPID_PUBLIC_KEY = os.path.join(BASE_DIR, 'vapid_public.pem')
VAPID_CLAIMS = {
    "sub": "mailto:federico.-torres@hotmail.com"
}
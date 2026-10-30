"""
Django settings for the Care Anmore website.

Settings are read from environment variables so the same code runs in
development and production. Copy `.env.example` to `.env` (or set the
variables in your hosting platform) before deploying.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path):
    """Minimal .env loader so no extra dependency is required."""
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(BASE_DIR / '.env')


def env(key, default=None):
    return os.environ.get(key, default)


def env_bool(key, default=False):
    return str(os.environ.get(key, default)).lower() in ('1', 'true', 'yes', 'on')


def env_list(key, default=''):
    return [item.strip() for item in os.environ.get(key, default).split(',') if item.strip()]


# --------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------
SECRET_KEY = env(
    'DJANGO_SECRET_KEY',
    'django-insecure-!#ip8z=ubnj-4l$1c%x$1u$)$c*8bcfss+f^3ojf&^b7r75vx1',
)
DEBUG = env_bool('DJANGO_DEBUG', True)
ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1],ungossiping-violette-nodose.ngrok-free.dev ')
CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS', '')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.humanize',
    'careweb.apps.CarewebConfig',
    'careapp.apps.CareappConfig',
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

# Serve compressed static files directly from Django when WhiteNoise is installed.
try:
    import whitenoise  # noqa: F401
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    _HAS_WHITENOISE = True
except ImportError:
    _HAS_WHITENOISE = False

ROOT_URLCONF = 'careanmor.urls'

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
                'careweb.context_processors.site_context',
                'careapp.context_processors.dashboard_nav',
            ],
        },
    },
]

WSGI_APPLICATION = 'careanmor.wsgi.application'
ASGI_APPLICATION = 'careanmor.asgi.application'

# --------------------------------------------------------------------------
# Database
# SQLite by default. Set DATABASE_ENGINE etc. to switch to PostgreSQL/MySQL.
# --------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': env('DATABASE_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': env('DATABASE_NAME', str(BASE_DIR / 'db.sqlite3')),
        'USER': env('DATABASE_USER', ''),
        'PASSWORD': env('DATABASE_PASSWORD', ''),
        'HOST': env('DATABASE_HOST', ''),
        'PORT': env('DATABASE_PORT', ''),
        'CONN_MAX_AGE': int(env('DATABASE_CONN_MAX_AGE', '60')),
    }
}

# --------------------------------------------------------------------------
# Cache (local memory by default; set CACHE_URL-style backend in production)
# --------------------------------------------------------------------------
CACHES = {
    'default': {
        'BACKEND': env('CACHE_BACKEND', 'django.core.cache.backends.locmem.LocMemCache'),
        'LOCATION': env('CACHE_LOCATION', 'careanmore'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --------------------------------------------------------------------------
# Internationalisation (UK)
# --------------------------------------------------------------------------
LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Europe/London'
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------
# Static and media files
# --------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {
        'BACKEND': (
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
            if (_HAS_WHITENOISE and not DEBUG)
            else 'django.contrib.staticfiles.storage.StaticFilesStorage'
        ),
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'careapp:login'

# --------------------------------------------------------------------------
# Sign-in and bot protection (see careweb/security.py)
# --------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = ['careweb.security.LockoutModelBackend']
LOGIN_FAILURE_LIMIT = int(env('LOGIN_FAILURE_LIMIT', '5'))        # failed tries per username + IP
LOGIN_LOCKOUT_MINUTES = int(env('LOGIN_LOCKOUT_MINUTES', '15'))
ENQUIRY_RATE_LIMIT = (int(env('ENQUIRY_RATE_LIMIT', '5')), 3600)  # enquiries per IP per hour
FORM_MIN_SECONDS = int(env('FORM_MIN_SECONDS', '3'))             # faster than this = bot
TURNSTILE_SITE_KEY = env('TURNSTILE_SITE_KEY', '')               # optional Cloudflare Turnstile
TURNSTILE_SECRET_KEY = env('TURNSTILE_SECRET_KEY', '')
# Behind a proxy or tunnel (ngrok, Nginx, a PaaS) set this so rate limits see real visitor IPs.
TRUST_X_FORWARDED_FOR = env_bool('DJANGO_TRUST_X_FORWARDED_FOR', False)
ADMIN_URL = env('DJANGO_ADMIN_URL', 'admin/')                    # e.g. 'office-7f3k/' hides admin from bots

SESSION_COOKIE_AGE = 8 * 3600          # sign out after 8 hours
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
LOGIN_REDIRECT_URL = 'careapp:dashboard'
# Uploads (logos, photos) are capped at 5 MB each
DATA_UPLOAD_MAX_MEMORY_SIZE = FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# --------------------------------------------------------------------------
# Email (enquiry notifications). Console backend prints emails in development.
# --------------------------------------------------------------------------
EMAIL_BACKEND = env('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', '')
EMAIL_PORT = int(env('EMAIL_PORT', '587'))
EMAIL_HOST_USER = env('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'Care Anmore website <no-reply@localhost>')
ENQUIRY_NOTIFY_EMAILS = env_list('ENQUIRY_NOTIFY_EMAILS', '')

# --------------------------------------------------------------------------
# Security hardening for production
# --------------------------------------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(env('DJANGO_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    X_FRAME_OPTIONS = 'DENY'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'loggers': {
        'careweb': {'handlers': ['console'], 'level': env('LOG_LEVEL', 'INFO')},
    },
}

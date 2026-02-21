"""MindArena — Production Settings"""
import os
import dj_database_url
import sentry_sdk
from .base import *  # noqa: F401,F403

DEBUG = False

_db_url = os.environ.get('DATABASE_URL')
if _db_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=_db_url,
            conn_max_age=600,
        )
    }
else:
    # Fallback to SQLite if no DATABASE_URL (initial Railway deploy)
    # Use /tmp for writable filesystem on containerized platforms
    import tempfile
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(tempfile.gettempdir(), 'mindarena.sqlite3'),
        }
    }

# Security — Railway healthcheck uses HTTP internally, so conditionally redirect
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'true').lower() == 'true'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Tighter ALLOWED_HOSTS in production
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '.railway.app').split(',')

# CORS — allow Railway domain and Godot clients
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^https://.*\.railway\.app$',
]
CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL', 'false').lower() == 'true'

# Sentry
sentry_dsn = os.environ.get('SENTRY_DSN')
if sentry_dsn:
    sentry_sdk.init(dsn=sentry_dsn, traces_sample_rate=0.1)

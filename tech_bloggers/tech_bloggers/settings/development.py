"""
Development settings for tech_bloggers project.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Development: Always allow localhost and 127.0.0.1
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Optionally add additional hosts from environment variable
env_hosts = os.getenv('DJANGO_ALLOWED_HOSTS', '')
if env_hosts:
    # Split and filter out empty strings
    additional_hosts = [h.strip() for h in env_hosts.split(',') if h.strip()]
    ALLOWED_HOSTS.extend(additional_hosts)

# Add testserver for Django test client
if 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')


# Database - SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Cache configuration for rate limiting - Local memory cache for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Email configuration - Console backend for development
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND') or 'django.core.mail.backends.console.EmailBackend'

# Logging Configuration
DEV_LOGGING_ENABLED = os.getenv('DEV_LOGGING_ENABLED', 'False').lower() == 'true'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'tech_bloggers.log',
            'formatter': 'verbose',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,      # Keep 5 backup files
            'encoding': 'utf-8',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        # Django's default logging
        'django': {
            'handlers': ['console', 'file'] if DEV_LOGGING_ENABLED else ['console'],
            'level': 'INFO',
        },
        # Our application logging
        'apps': {
            'handlers': ['console', 'file'] if DEV_LOGGING_ENABLED else ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Development-specific security settings (relaxed)
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False


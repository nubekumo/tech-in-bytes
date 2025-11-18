"""
Base Django settings for tech_bloggers project.
Common settings shared between development and production.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# Note: BASE_DIR now points to the project root (one level up from settings directory)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# This will be overridden in development.py and production.py
DEBUG = False

# This will be overridden in development.py and production.py
ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'csp',
    'taggit',
    'easy_thumbnails',
    'image_cropping',
    'django_bleach',
    'axes',
    # 2FA apps
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'two_factor',
    'apps.accounts',
    'apps.blog',
    'apps.pages',
    'apps.core',
]

# Image cropping settings
from easy_thumbnails.conf import Settings as thumbnail_settings
THUMBNAIL_PROCESSORS = (
    'image_cropping.thumbnail_processors.crop_corners',
) + thumbnail_settings.THUMBNAIL_PROCESSORS

IMAGE_CROPPING_BACKEND = 'image_cropping.backends.easy_thumbnails.EasyThumbnailsBackend'
IMAGE_CROPPING_BACKEND_PARAMS = {}

# Additional image cropping settings
IMAGE_CROPPING_SIZE_WARNING = True
IMAGE_CROPPING_THUMB_SIZE = (300, 300)
IMAGE_CROPPING_MIN_SIZE = [20, 20]

# Image upload security limits
# Max upload size in megabytes
IMAGE_MAX_UPLOAD_MB = int(os.getenv('IMAGE_MAX_UPLOAD_MB', '2'))
# Maximum allowed dimensions
IMAGE_MAX_WIDTH = int(os.getenv('IMAGE_MAX_WIDTH', '2048'))
IMAGE_MAX_HEIGHT = int(os.getenv('IMAGE_MAX_HEIGHT', '2048'))
# Maximum total pixels to mitigate decompression bombs
IMAGE_MAX_PIXELS = int(os.getenv('IMAGE_MAX_PIXELS', '12000000'))  # 12 MP

# Image upload quantity and storage limits
MAX_IMAGES_PER_POST = int(os.getenv('MAX_IMAGES_PER_POST', '15'))  # Max images per blog post
MAX_IMAGES_PER_USER = int(os.getenv('MAX_IMAGES_PER_USER', '50'))  # Max total images per user
MAX_STORAGE_PER_USER_MB = int(os.getenv('MAX_STORAGE_PER_USER_MB', '400'))  # Max storage per user in MB
ORPHANED_IMAGE_CLEANUP_HOURS = int(os.getenv('ORPHANED_IMAGE_CLEANUP_HOURS', '12'))  # Hours before orphaned images are cleaned up

MIDDLEWARE = [
    'csp.middleware.CSPMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'axes.middleware.AxesMiddleware',
    'apps.accounts.middleware.SecureSessionMiddleware', # Added for secure session handling
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tech_bloggers.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"], # Global templated dir
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tech_bloggers.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
# This will be overridden in development.py and production.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# Email configuration
# Will be overridden in development.py and production.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

# Password reset settings
PASSWORD_RESET_TIMEOUT = 86400  # 24 hours in seconds
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@tech-bloggers.local')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django Admin Site Configuration
ADMIN_SITE_HEADER = "Tech-In-Bytes Administration"
ADMIN_SITE_TITLE = "Tech-In-Bytes Admin"
ADMIN_INDEX_TITLE = "Welcome to Tech-In-Bytes Administration"

# Authentication settings
LOGIN_REDIRECT_URL = 'pages:index'
LOGIN_URL = 'accounts:login'
LOGOUT_URL = 'accounts:logout'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# 2FA Configuration
TWO_FACTOR_CALL_GATEWAY = None  # We're not using phone calls
TWO_FACTOR_SMS_GATEWAY = None   # We're not using SMS
TWO_FACTOR_LOGIN_URL = 'accounts:login'
TWO_FACTOR_SETUP_URL = 'accounts:two_factor:setup'
TWO_FACTOR_BACKUP_TOKENS_URL = 'accounts:two_factor:backup_tokens'
TWO_FACTOR_REMOVE_URL = 'accounts:two_factor:disable'

# Axes configuration: lock after 5 failures for 1 hour, keyed by username only
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(hours=1)
AXES_LOCKOUT_PARAMETERS = [['username']]  # Lock by username only, not IP
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = 'accounts/lockout.html'

# Exclude 2FA URLs from Axes rate limiting to avoid conflicts
AXES_EXCLUDE_URLS = [
    '/accounts/two_factor/',
    '/accounts/two_factor/setup/',
    '/accounts/two_factor/backup_tokens/',
    '/accounts/two_factor/disable/',
    '/accounts/two_factor/qr/',
]

# Sites framework
SITE_ID = 1

# Static assets version for cache busting
STATIC_VERSION = '4.2'

# Bleach Configuration
BLEACH_ALLOWED_TAGS = [
    "p", "br", "hr", "div",       # paragraphs, line breaks, and divs
    "b", "i", "u", "em", "strong", "span",  # inline formatting
    "a",                          # links
    "ul", "ol", "li",             # lists
    "blockquote", "code", "pre",  # quotes & code
    "img",                        # images
    "h1", "h2", "h3",             # headings
    "font",                       # font styling (for font-family, font-size)
    "table", "thead", "tbody", "tr", "th", "td",  # tables
]

BLEACH_ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel", "target"],   # safe link attrs
    "img": ["src", "alt", "title", "width", "height"],  # images with size attributes
    "span": ["style"],                         # allow inline style for span
    "font": ["face", "size", "color", "style"], # font attributes including style
    "p": ["style"],                            # paragraph styling (for line-height, text-align)
    "b": ["style"],                            # bold text with styling
    "i": ["style"],                            # italic text with styling
    "u": ["style"],                            # underlined text with styling
    "em": ["style"],                           # emphasized text with styling
    "strong": ["style"],                       # strong text with styling
    "div": ["style"],                          # div styling (for text-align)
    "table": ["style", "border", "cellpadding", "cellspacing"],  # table attributes
    "td": ["style", "colspan", "rowspan"],     # table cell attributes
    "th": ["style", "colspan", "rowspan"],     # table header attributes
    "code": ["class"],                          # code tags
    "pre": ["class"],                           # pre tags for code blocks
}

# Allow specific CSS styles for formatting
BLEACH_ALLOWED_STYLES = [
    'text-decoration',  # for underline
    'text-align',       # for text alignment
    'border',           # for table borders
    'border-collapse',  # for table styling
    'border-spacing',   # for table spacing
    'padding',          # for table cell padding
    'margin',           # for spacing
    'margin-left',      # for table alignment
    'margin-right',     # for table alignment
    'margin-top',       # for vertical spacing
    'margin-bottom',    # for vertical spacing
    'float',            # for table left/right alignment
    'color',            # for text color
    'background-color', # for background color
    'font-family',      # for font styling
    'font-size',        # for font size
    'font-weight',      # for bold
    'font-style',       # for italic
    'line-height',      # for line spacing
    'width',            # for element width
    'height',           # for element height
]

BLEACH_ALLOWED_PROTOCOLS = ["http", "https", "mailto"]  # disallow javascript:

# Additional Bleach settings
BLEACH_STRIP_TAGS = False  # Don't strip tags, just escape
BLEACH_STRIP_COMMENTS = True  # Strip HTML comments

# Content Security Policy (CSP) - django-csp 4.0+ configuration
# Note: TinyMCE (third-party library) uses inline scripts that cannot be avoided.
# These are reported but don't affect functionality in report-only mode.
# For production, consider self-hosting TinyMCE or using CSP hashes.
CONTENT_SECURITY_POLICY_REPORT_ONLY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'style-src': ("'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com", "https://cdn.jsdelivr.net"),
        'script-src': ("'self'", "https://cdn.jsdelivr.net"),
        'img-src': ("'self'", "data:", "https:"),
        'font-src': ("'self'", "https://cdnjs.cloudflare.com"),
        'connect-src': ("'self'",),
        'frame-ancestors': ("'none'",),
        'base-uri': ("'self'",),
        'form-action': ("'self'",),
    }
}


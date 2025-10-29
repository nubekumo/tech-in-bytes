"""
Django settings initialization.
Loads the appropriate settings module based on DJANGO_ENV environment variable.
"""
import os

# Determine which settings to use based on environment
env = os.getenv('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *
else:
    from .development import *


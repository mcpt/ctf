from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

ALLOWED_HOSTS = ['localhost']

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STATIC_ROOT = '/app-static'

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = '/app-media'
MEDIA_URL = '/media/'

try:
    from mCTF.config2 import *
except ImportError:
    raise TypeError("Please create a config file to override values in config2.py")

CSRF_TRUSTED_ORIGINS = list(f'https://{host}' for host in ALLOWED_HOSTS)

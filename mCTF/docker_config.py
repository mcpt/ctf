from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = True
ALLOWED_HOSTS = ['localhost', "172.19.143.136"]

STATIC_ROOT = '/app-static'

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
MEDIA_ROOT = '/app-media'
MEDIA_URL = '/media/'

ROOT = "http://localhost:28730"  # Change this to your domain

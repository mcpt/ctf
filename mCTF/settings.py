"""
Django settings for mCTF project.

Generated by 'django-admin startproject' using Django 3.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "<replace>"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.redirects",
    "django.contrib.flatpages",
    "django.contrib.humanize",
    "gameserver",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "providers.kyii",
    "django_bootstrap5",
    "sass_processor",
    "adminsortable2",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "gameserver.middleware.TimezoneMiddleware",
    "gameserver.middleware.ContestMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
    "gameserver.middleware.RedirectFallbackTemporaryMiddleware",
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

ROOT_URLCONF = "mCTF.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "gameserver.context_processors.settings_context",
            ],
        },
    },
]

WSGI_APPLICATION = "mCTF.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "sass_processor.finders.CssFinder",
]
STATICFILES_DIRS = [
    BASE_DIR / "public",
]


# Auth settings

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_USER_MODEL = "gameserver.User"

LOGIN_REDIRECT_URL = "/accounts/profile"

LOGOUT_REDIRECT_URL = "/"

# ACCOUNT_ACTIVATION_DAYS = 7
# REGISTRATION_OPEN = True
# REGISTRATION_SALT = '<registration salt here>'

ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_SIGNUP_REDIRECT_URL = "/"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

ACCOUNT_FORMS = {"signup": "gameserver.forms.MCTFSignupForm"}

TOS_URL = "/tos"


# Email settings

EMAIL_BACKEND = "<your email backend>"


# S3 STORAGE CONFIGURATION
# FOLLOW https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
DEFAULT_FILE_STORAGE = ""
AWS_S3_REGION_NAME = ""
AWS_S3_ENDPOINT_URL = ""
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
AWS_STORAGE_BUCKET_NAME = ""
AWS_S3_FILE_OVERWRITE = False

STATICFILES_STORAGE = ""


# NavBar settings

NAVBAR = {
    "Problems": "/problems/",
    "Submissions": "/submissions/",
    "Users": "/users/",
    "Teams": "/teams/",
    "Organizations": "/organizations/",
    "Contests": "/contests/",
}


# Meta tag settings

DESCRIPTION = (
    "mCTF is a open-source online platform for people to host or participate in CTF contests."
)
KEYWORDS = [
    "mCTF",
    "MCPT",
    "WLMOJ",
    "ctf",
    "open source",
    "online judge",
    "online platform",
    "cybersecurity",
]
SCHEME = "https"


# Sass settings

SASS_PROCESSOR_ROOT = STATIC_ROOT
SASS_PROCESSOR_AUTO_INCLUDE = False
SASS_PRECISION = 8
SASS_OUTPUT_STYLE = "compact"


# Challenge Deployment settings

CHALLENGE_CLUSTER = {
    "connection": {
        "host": None,
        "token": "",
        "caCert": BASE_DIR / "mCTF" / "cluster_ca.crt",
    },
    "namespace": "mctf-chall",
    "domain": "{}.example.com",
    "imagePullSecrets": {},
    "runtimeClassNames": {
        "default": None,
        "gvisor": "runsc",
        "kata": "kata",
    },
    "securityContexts": {
        "default": {},
        "redpwn": {
            "seccompProfile": {"type": "Unconfined"},
            "apparmorProfile": {"type": "Unconfined"},
            "capabilities": {
                "add": [
                    "CHOWN",
                    "SETUID",
                    "SETGID",
                    "SYS_ADMIN",
                ],
                "drop": [
                    "AUDIT_WRITE",
                    "DAC_OVERRIDE",
                    "FOWNER",
                    "FSETID",
                    "KILL",
                    "MKNOD",
                    "NET_BIND_SERVICE",
                    "NET_RAW",
                    "SETFCAP",
                    "SETPCAP",
                    "SYS_CHROOT",
                ],
            },
        },
    },
}


# Other settings

SITE_ID = 1

ROOT = "http://localhost"  # Change this to your domain

SILENCED_SYSTEM_CHECKS = ["urls.W002"]

DEFAULT_TIMEZONE = "UTC"

try:
    from mCTF.config import *
except ImportError:
    print("Please create a config file to override values in settings.py")

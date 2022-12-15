"""
    Production Django settings for Pulsifi project.

    Generated by 'django-admin startproject' using Django 4.1.3.
"""

from os import getenv as os_getenv
from pathlib import Path

from django.urls import reverse_lazy

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
ALLOWED_HOSTS = [os_getenv("ALLOWED_HOSTS")]
ALLOWED_ORIGINS = [os_getenv("ALLOWED_ORIGINS")]  # TODO: work out how to host site
CSRF_TRUSTED_ORIGINS = ALLOWED_ORIGINS.copy()
STATIC_ROOT = "/staticfiles/"
STATIC_URL = "static/"
MEDIA_ROOT = BASE_DIR / r"pulsifi\media"
MEDIA_URL = "media/"


LOGIN_URL = reverse_lazy("pulsifi:home")
LOGIN_REDIRECT_URL = reverse_lazy("pulsifi:feed")
LOGOUT_REDIRECT_URL = reverse_lazy("default")

ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_PRESERVE_USERNAME_CASING = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_USERNAME_MIN_LENGTH = 4
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 1
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_FORMS = {"signup": "pulsifi.forms.SignupForm"}
AVATAR_GRAVATAR_DEFAULT = "mp"

MESSAGE_DISPLAY_LENGTH = os_getenv("MESSAGE_DISPLAY_LENGTH")
FOLLOWER_COUNT_SCALING_FUNCTION = os_getenv("FOLLOWER_COUNT_SCALING_FUNCTION")


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-6dsvxca6m@u%(fqvlzz1*=6utyg-%^ha+zyr4n_!+hu0xe-7u#"  # noqa


# Application definition

INSTALLED_APPS = [
    "pulsifi.apps.PulsifiConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",  # noqa
    "allauth.socialaccount.providers.discord",  # noqa
    "allauth.socialaccount.providers.facebook",  # noqa
    "allauth.socialaccount.providers.github",  # noqa
    "allauth.socialaccount.providers.google",  # noqa
    "allauth.socialaccount.providers.microsoft",  # noqa
    "allauth.socialaccount.providers.reddit",  # noqa
    "allauth.socialaccount.providers.stackexchange",  # noqa
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "allauth_2fa",
    "avatar"
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth_2fa.middleware.AllauthTwoFactorMiddleware",
]

WSGI_APPLICATION = "core.wsgi.application"

ROOT_URLCONF = "core.urls"

SITE_ID = 1

ACCOUNT_ADAPTER = "allauth_2fa.adapter.OTPAdapter"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages"
            ]
        }
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3"
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend'
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"
    }
]


LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_L10N = True
USE_TZ = True
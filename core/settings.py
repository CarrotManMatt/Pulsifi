"""
    Django settings for Pulsifi project.

    Partially generated by 'django-admin startproject' using Django 4.1.3.
"""

import datetime
import re as regex
from pathlib import Path

import tldextract
from django import urls as django_urls
from django.core.exceptions import ImproperlyConfigured
from environ import Env

from core import utils as core_url_utils

# Build paths inside the project like this: BASE_DIR / "subdir"
BASE_DIR = Path(__file__).resolve().parent.parent

# Adding additional (not manually specified) environment variables as settings values
Env.read_env(BASE_DIR / ".env")

# noinspection SpellCheckingInspection
env = Env(
    PRODUCTION=(bool, True),
    USERNAME_MIN_LENGTH=(int, 4),
    ACCOUNT_EMAIL_VERIFICATION=(str, "mandatory"),
    ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS=(int, 1),
    AVATAR_GRAVATAR_DEFAULT=(str, "mp"),
    VERSION=(str, "0.1"),
    EMAIL_HOST=(str, "smtppro.zoho.eu"),
    EMAIL_PORT=(int, 465),
    EMAIL_HOST_USER=(str, "no-reply@pulsifi.tech"),
    EMAIL_USE_SSL=(bool, True),
    PULSIFI_ADMIN_COUNT=(int, 1),
    MESSAGE_DISPLAY_LENGTH=(int, 15),
    MIN_TIME_BETWEEN_REPLIES_ON_SAME_POST=(float, 3.0),
    FOLLOWER_COUNT_SCALING_FUNCTION=(str, "linear"),
    PASSWORD_SIMILARITY_TO_USER_ATTRIBUTES=(float, 0.627),
    USERNAME_SIMILARITY_PERCENTAGE=(int, 87),
    RESTRICTED_ADMIN_USERNAMES=(list, ["pulsifi"]),
    CUSTOM_RESERVED_USERNAMES=(list, ["puls", "reply"]),
    TEST_DATA_JSON_FILE_PATH=(str, None)
)

if env("PRODUCTION"):
    prod_env = Env(
        ALLOWED_HOSTS=(list, ["pulsifi"]),
        ALLOWED_ORIGINS=(list, ["https://pulsifi.tech"]),
        LOG_LEVEL=(str, "WARNING")
    )

    _temp_log_level = prod_env("LOG_LEVEL").upper()

    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = False

    # Namespace resolving settings
    ALLOWED_HOSTS = prod_env("ALLOWED_HOSTS")
    ALLOWED_ORIGINS = prod_env("ALLOWED_ORIGINS")  # TODO: work out how to host site
    CSRF_TRUSTED_ORIGINS = ALLOWED_ORIGINS.copy()
else:
    dev_env = Env(
        DEBUG=(bool, True),
        ALLOWED_HOSTS=(list, ["localhost"]),
        LOG_LEVEL=(str, "INFO")
    )

    _temp_log_level = dev_env("LOG_LEVEL").upper()

    DEBUG = dev_env("DEBUG")

    # Namespace resolving settings
    ALLOWED_HOSTS = dev_env("ALLOWED_HOSTS")

# Confirming that the supplied environment variable values for these settings are one of the valid choices
if not env("USERNAME_MIN_LENGTH") > 1:
    raise ImproperlyConfigured("USERNAME_MIN_LENGTH must be an integer greater than 1.")
_ACCOUNT_EMAIL_VERIFICATION_choices = ("mandatory", "optional", "none")
if env("ACCOUNT_EMAIL_VERIFICATION") not in _ACCOUNT_EMAIL_VERIFICATION_choices:
    raise ImproperlyConfigured(f"ACCOUNT_EMAIL_VERIFICATION must be one of {_ACCOUNT_EMAIL_VERIFICATION_choices}.")
if not env("ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS") > 0:
    raise ImproperlyConfigured("ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS must be an integer greater than 0.")
# noinspection SpellCheckingInspection
_AVATAR_GRAVATAR_DEFAULT_choices = ("404", "mp", "identicon", "monsterid", "wavatar", "retro", "robohash")
if env("AVATAR_GRAVATAR_DEFAULT") not in _AVATAR_GRAVATAR_DEFAULT_choices:
    raise ImproperlyConfigured(f"AVATAR_GRAVATAR_DEFAULT must be one of {_AVATAR_GRAVATAR_DEFAULT_choices}.")
if regex.search(r"^\d*(?:\.\d*)+$", env("VERSION")) is None:
    raise ImproperlyConfigured("VERSION must be in this format: \"<number>.<number>.<number>\".")
if not tldextract.extract(env("EMAIL_HOST")).domain or not tldextract.extract(env("EMAIL_HOST")).suffix:
    raise ImproperlyConfigured("EMAIL_HOST must be a a valid email host name with a valid domain name & suffix.")
if not 0 < env("EMAIL_PORT") <= 65535:
    raise ImproperlyConfigured("EMAIL_PORT must be a valid port number (an integer between 0 and 65536).")
_EMAIL_HOST_USER_domain: str = env("EMAIL_HOST_USER").rpartition("@")[2]
if env("EMAIL_HOST_USER").count("@") != 1 or (env("EMAIL_HOST_USER").count("@") == 1 and (not tldextract.extract(_EMAIL_HOST_USER_domain).domain or not tldextract.extract(_EMAIL_HOST_USER_domain).suffix)):
    raise ImproperlyConfigured("EMAIL_HOST_USER must be a valid email address.")
if not env("PULSIFI_ADMIN_COUNT") > 0:
    raise ImproperlyConfigured("PULSIFI_ADMIN_COUNT must be an integer greater than 0.")
if not env("MESSAGE_DISPLAY_LENGTH") > 0:
    raise ImproperlyConfigured("MESSAGE_DISPLAY_LENGTH must be an integer greater than 0.")
if not 1.0 <= env("MIN_TIME_BETWEEN_REPLIES_ON_SAME_POST") <= 2880.0:
    raise ImproperlyConfigured("MIN_TIME_BETWEEN_REPLIES_ON_SAME_POST must be a float between 1.0 and 2880.0 (representing the number of minutes).")
_FOLLOWER_COUNT_SCALING_FUNCTION_choices = ("logarithmic", "linear", "quadratic", "linearithmic", "exponential", "factorial")
if env("FOLLOWER_COUNT_SCALING_FUNCTION") not in _FOLLOWER_COUNT_SCALING_FUNCTION_choices:
    raise ImproperlyConfigured(f"FOLLOWER_COUNT_SCALING_FUNCTION must be one of {_FOLLOWER_COUNT_SCALING_FUNCTION_choices}.")
if not 0.1 <= env("PASSWORD_SIMILARITY_TO_USER_ATTRIBUTES") <= 1.0:
    raise ImproperlyConfigured("PASSWORD_SIMILARITY_TO_USER_ATTRIBUTES must be a float between 0.1 and 1.0.")
if not 20 <= env("USERNAME_SIMILARITY_PERCENTAGE") <= 100:
    raise ImproperlyConfigured("USERNAME_SIMILARITY_PERCENTAGE must be an integer between 20 and 100.")
_LOG_LEVEL_choices = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
if _temp_log_level not in _LOG_LEVEL_choices:
    raise ImproperlyConfigured(f"LOG_LEVEL must be one of {_LOG_LEVEL_choices}")


def _display_user(user) -> str:
    return str(user)


STATIC_ROOT = "/staticfiles/"
STATIC_URL = "static/"
MEDIA_ROOT = BASE_DIR / r"pulsifi\media"
MEDIA_URL = "media/"

# Default URL redirect settings (used for authentication)
LOGIN_URL = core_url_utils.reverse_url_with_get_params_lazy(
    "pulsifi:home",
    get_params={"action": "login"}
)
LOGIN_REDIRECT_URL = django_urls.reverse_lazy("pulsifi:feed")  # TODO: dont need to reverse
LOGOUT_REDIRECT_URL = django_urls.reverse_lazy("default")  # TODO: dont need to reverse
SIGNUP_URL = core_url_utils.reverse_url_with_get_params_lazy(
    "pulsifi:home",
    get_params={"action": "signup"}
)

# Auth model settings
AUTH_USER_MODEL = "pulsifi.User"

# Authentication configuration settings (mainly for allauth & its associated packages)
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_PRESERVE_USERNAME_CASING = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_USER_DISPLAY = _display_user
ACCOUNT_USERNAME_MIN_LENGTH = env("USERNAME_MIN_LENGTH")
ACCOUNT_EMAIL_VERIFICATION = env("ACCOUNT_EMAIL_VERIFICATION")
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = env("ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS")
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_FORMS = {
    "login": "pulsifi.forms.Login_Form",
    "signup": "pulsifi.forms.Signup_Form"
}
AVATAR_GRAVATAR_DEFAULT = env("AVATAR_GRAVATAR_DEFAULT")
AVATAR_PROVIDERS = (
    "avatar.providers.PrimaryAvatarProvider",
    "pulsifi.avatar_providers.DiscordAvatarProvider",
    "pulsifi.avatar_providers.GithubAvatarProvider",
    "pulsifi.avatar_providers.GoogleAvatarProvider",
    "avatar.providers.GravatarAvatarProvider"
)
AVATAR_AUTO_GENERATE_SIZES = (100, 150)
# noinspection SpellCheckingInspection
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "VERIFIED_EMAIL": True,
        "APP": {
            "name": "Google",
            "client_id": "661911946943-ttrstdi5luvlfcee625gq71ikekk7qcg.apps.googleusercontent.com",
            "secret": env("OATH_GOOGLE_SECRET"),
            "key": ""
        }
    },
    "discord": {
        "VERIFIED_EMAIL": True,
        "APP": {
            "name": "Discord",
            "client_id": "1054763384391876628",
            "secret": env("OATH_DISCORD_SECRET"),
            "key": ""
        }
    },
    "github": {
        "VERIFIED_EMAIL": True,
        "APP": {
            "name": "GitHub",
            "client_id": "3c53e63beb0fb9cfcce3",
            "secret": env("OATH_GITHUB_SECRET"),
            "key": ""
        }
    },
    "microsoft": {
        "VERIFIED_EMAIL": True,
        "APP": {
            "name": "Microsoft",
            "client_id": "6f9ee230-1fc5-4d18-ace3-a45805cc4112",
            "secret": env("OATH_MICROSOFT_SECRET"),
            "key": ""
        }
    }
}

# Email settings to configure how Django should send emails
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_SSL = env("EMAIL_USE_SSL")

# Custom settings values (used to control functionality of the app)
PULSIFI_ADMIN_COUNT = env("PULSIFI_ADMIN_COUNT")
MESSAGE_DISPLAY_LENGTH = env("MESSAGE_DISPLAY_LENGTH")
MIN_TIME_BETWEEN_REPLIES_ON_SAME_POST = datetime.timedelta(minutes=env("MIN_TIME_BETWEEN_REPLIES_ON_SAME_POST"))
USERNAME_SIMILARITY_PERCENTAGE = env("USERNAME_SIMILARITY_PERCENTAGE")
RESTRICTED_ADMIN_USERNAMES = set(env("RESTRICTED_ADMIN_USERNAMES"))
CUSTOM_RESERVED_USERNAMES = set(env("CUSTOM_RESERVED_USERNAMES"))
FOLLOWER_COUNT_SCALING_FUNCTION = env("FOLLOWER_COUNT_SCALING_FUNCTION")  # TODO: Add function for how delete time of pulses & replies scales with follower count (y=log_2(x+1), y=x, y=xlog_2(x+1), y=2^x-1, y=(x+1)!-1)

# Tests settings
TEST_DATA_JSON_FILE_PATH = None
if env("TEST_DATA_JSON_FILE_PATH"):
    TEST_DATA_JSON_FILE_PATH = Path(env("TEST_DATA_JSON_FILE_PATH"))

# Logging settings
# noinspection SpellCheckingInspection
LOGGING = {
    "version": 1,
    "formatters": {
        "pulsifi": {
            "format": "{levelname} - {module}: {message}",
            "style": "{"
        },
        "web_server": {
            "format": "[{asctime}] {message}",
            "datefmt": "%d/%b/%Y %H:%M:%S",
            "style": "{"
        }
    },
    "handlers": {
        "pulsifi": {
            "class": "logging.StreamHandler",
            "formatter": "pulsifi"
        },
        "web_server": {
            "class": "logging.StreamHandler",
            "formatter": "web_server"
        }
    },
    "loggers": {
        "django.server": {
            "handlers": ["web_server"],
            "level": _temp_log_level
        }
    },
    "root": {"handlers": ["pulsifi"], "level": _temp_log_level}
}

# Secret key that is used for important secret stuff (keep the one used in production a secret!)
SECRET_KEY = env("SECRET_KEY")

# App definitions
# noinspection SpellCheckingInspection
INSTALLED_APPS = [
    "pulsifi.apps.PulsifiConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.admindocs",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.discord",
    "allauth.socialaccount.providers.github",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.microsoft",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "allauth_2fa",
    "avatar",
    "rangefilter"
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

# noinspection PyUnresolvedReferences
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

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend'
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {
            "user_attributes": ("username", "email", "bio"),
            "max_similarity": env("PASSWORD_SIMILARITY_TO_USER_ATTRIBUTES")
        }
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

# Language & time settings
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

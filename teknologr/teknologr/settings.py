"""
Django settings for teknologr project.

Generated by 'django-admin startproject' using Django 1.9.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import locale
from getenv import env
import dj_database_url

import ldap
from django_auth_ldap.config import LDAPSearch, PosixGroupType


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_DIR = os.path.dirname(__file__)

TEST_PEP8_DIRS = [os.path.dirname(PROJECT_DIR), ]

# PEP8
TEST_PEP8_EXCLUDE = ['migrations', ]  # Exclude this paths from tests
TEST_PEP8_IGNORE = [
    'E226', # Whitespace around arithmetic operators
    'E266', # Leading amount of '#' in comment
    'E261', # Spaces before inline comments
    'E302', # Blank lines
    'E501', # Line lengths
    'E731', # Lambda expression assignments
]
TEST_PEP8_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'setup.cfg')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', 'secret_key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', True)


'''
If a proxy (or similar) is used to handle requests to Teknologr, the request can be modified in some ways which can have unwanted side-effects in Django.

One such problem occurs when an absoule uri (to for example /api/members/) is being built by Django, because the host name is taken from a request. If that request have been forwarded by some proxy it's 'HTTP_HOST' header will no longer be the orignal host name (let's say teknologr.com) but instead for example localhost:8000. The resulting uri is then 'http://localhost:8000/api/members/' while the correct uri is 'https://teknolog.com/api/members/'.

The solution is to instead read the host name from the 'X-Forwarded-Host' (https://http.dev/x-forwarded-host) header in the request, which should be set by the proxy to the target host, as specified by the reqeust originator, if the request is forwarded. This is done in Django using the USE_X_FORWARDED_HOST setting.

However, this will only resolve the problem with the host name, not the protocol part of the uri. Since the forwarded request can be done with HTTP, even if the original request was made with HTTPS, Django migth incorrectly deduce that a request is not secure even if the orignal request was (or vice verca). Using the SECURE_PROXY_SSL_HEADER setting Django will look a the specified header (usually the 'X-Forwarded-Proto' header: https://http.dev/x-forwarded-proto) rather than the request url to deduce if a request is secure or not. Note that the header needs to be in the format as used by request.META, i.e. all caps and (most likely) prefixed with 'HTTP_'.
'''
ALLOWED_HOSTS = ['localhost'] + env('ALLOWED_HOSTS', [])

if env('IS_BEHIND_PROXY', False):
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'test_pep8',
    'rest_framework',
    'django_filters',
    'ajax_select',
    'members',
    'katalogen',
    'registration',
    'bootstrap4',
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

ROOT_URLCONF = 'teknologr.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'api/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'teknologr.wsgi.application'

# Logging
if not DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': env('LOG_FILE', '/var/log/teknologr/info.log'),
            },
        },
        'loggers': {
            'django': {
                'handlers': ['file'],
                'level': 'INFO',
                'propagate': True,
            },
        },
    }
'''
else:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
            }
        },
        'loggers': {
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'DEBUG',
            },
        },
    }
'''


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases
DATABASES = {
    'default': dj_database_url.parse(env('DATABASE', 'sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3')))
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'sv-fi'

TIME_ZONE = 'Europe/Helsinki'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Set the desired locale for string sorting
locale.setlocale(locale.LC_COLLATE, 'sv_FI.utf8')
# The sort order still depends on which method is used:
#  - order_by as is:                A a Ä Å Ö ä å ö (case sensitive and does not understand ÅÄÖ)
#  - order_by with Lower()/Upper(): A+a Ä Å Ö ä å ö (does not understand ÅÄÖ)
#  - sort() as is:                  A a Ä Å Ö ä å ö (case sensitive)
#  - sort() with .lower()/.upper(): A+a Ä+ä Å+å Ö+ö (all good except Ä comes before Å...)
#  - sort() locale.strxfrm:         A+a Å+å Ä+ä Ö+ö (OK)


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# REST Framework settings
# TODO: provide GET access to certain users for non-admins
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAdminUser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'api.utils.BrowsableAPIRendererWithoutForms',
        'rest_framework_csv.renderers.CSVRenderer',
    ),
    'DEFAULT_PAGINATION_CLASS': 'api.utils.Pagination',
}

# LDAP stuff

# Baseline configuration.
AUTH_LDAP_SERVER_URI = env("LDAP_SERVER_URI", "ldaps://localhost:45671")

AUTH_LDAP_USER_DN_TEMPLATE = env("LDAP_USER_DN_TEMPLATE", "uid=%(user)s,dc=example,dc=com")

# Set up the basic group parameters.
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    env("LDAP_GROUP_DN", "ou=group,dc=example,dc=com"),
    ldap.SCOPE_SUBTREE,
    "(objectClass=PosixGroupType)"
)
AUTH_LDAP_GROUP_TYPE = PosixGroupType(name_attr="cn")

# Populate the Django user from the LDAP directory.
AUTH_LDAP_USER_ATTR_MAP = {
    "username": "uid",
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail"
}

# Map LDAP group to is_staff property in Member model
# this restricts all is_staff required views to those that are members of the specified LDAP group
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_staff": env("LDAP_STAFF_GROUP_DN", "cn=admin,ou=group,dc=example,dc=com"),
}

# This is the default, but I like to be explicit.
AUTH_LDAP_ALWAYS_UPDATE_USER = True

# Use LDAP group membership to calculate group permissions.
AUTH_LDAP_FIND_GROUP_PERMS = True

# Cache group memberships for an hour to minimize LDAP traffic
AUTH_LDAP_CACHE_GROUPS = True
AUTH_LDAP_GROUP_CACHE_TIMEOUT = 3600


# Keep ModelBackend around for per-user permissions and maybe a local
# superuser.
AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# Never require cert
AUTH_LDAP_GLOBAL_OPTIONS = {
    ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER
}

# Confs nexsecary for ajax-select
AJAX_SELECT_INLINES = 'staticfiles'
STATIC_ROOT = env("STATIC_ROOT", None)

# Email conf
EMAIL_HOST = env("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = env("EMAIL_PORT", 587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", None)
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", None)
EMAIL_USE_TLS = env("EMAIL_USE_TLS", True)

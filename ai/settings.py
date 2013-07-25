# Django settings for ai project.
from datetime import timedelta
from celery.task.schedules import crontab 
import djcelery
djcelery.setup_loader()
import ldap
from django_auth_ldap.config import LDAPSearch

import os.path

# Import branched settings files
from local_settings import *
from merops_settings import *

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
PACKAGE_ROOT = os.path.abspath(os.path.dirname(__file__))

# SOUTH_TESTS_MIGRATE = False

MANAGERS = ADMINS


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PACKAGE_ROOT, "site_media", "static")

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(PACKAGE_ROOT, "static"),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
    #'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'notification.context_processors.notification',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'ai.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'ai.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PACKAGE_ROOT, "templates"),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.comments',
    'django.contrib.admin',

    'debug_toolbar',
    'crispy_forms',
    'django_filters',
    'south',
    'djcelery',
    'kombu.transport.django',
    'storages',
    'notification',

    'articleflow',
    'issues',
    'fancyauth',
    'notes',
    'crispycomments',
    'errors',
)

# Customizing contrib comments
COMMENTS_APP = 'crispycomments'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s:%(funcName)s:%(lineno)d | %(message)s'
        },
        'debugging': {
            'format': '%(levelname)s\t%(module)s:%(funcName)s\t%(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'tasks-file':{
            'level': 'DEBUG',
            'class':'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'filename': os.path.join(LOG_FILE_DIRECTORY, 'tasks.log'),
            'backupCount': '30',
            'formatter': 'verbose',
            },
        'celery-file':{
            'level': 'INFO',
            'class':'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'filename': os.path.join(LOG_FILE_DIRECTORY, 'celery.log'),
            'backupCount': '30',
            'formatter': 'verbose',
            },
        'requests-file':{
            'level': 'DEBUG',
            'class':'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'filename': os.path.join(LOG_FILE_DIRECTORY, 'requests.log'),
            'backupCount': '30',
            'formatter': 'verbose',
            },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            },
        'debugging': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'debugging',
            },
        'debugging-info': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'debugging',
            },
        'debugging-error': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'debugging',
            },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
            },
        'articleflow.management.commands.one_migration': {
            'handlers': ['debugging-info', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
            },
        'issues.views': {
            'handlers': ['debugging', 'requests-file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'errors.views': {
            'handlers': ['debugging'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'errors.models': {
            'handlers': ['debugging', 'requests-file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'articleflow.models': {
            'handlers': ['debugging', 'requests-file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'articleflow.templatetags.transitions': {
            'handlers': ['debugging', 'requests-file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'articleflow.transitionrules': {
            'handlers': ['debugging', 'requests-file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'articleflow.tests': {
            'handlers': ['debugging'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'articleflow.views': {
            'handlers': ['debugging', 'requests-file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'articleflow.views_api': {
            'handlers': ['debugging', 'requests-file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'articleflow.daemons.merops_tasks': {
            'handlers': ['debugging', 'tasks-file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'articleflow.daemons.transition_tasks': {
            'handlers': ['debugging', 'tasks-file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'articleflow.models': {
            'handlers': ['debugging', 'requests-file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'celery': {
            'handlers': ['debugging', 'celery-file'],
            'level': 'DEBUG',
            'propagate': True,
            },
        'commands': {
            'handlers': ['debugging'],
            'level': 'DEBUG',
            'propagate': True,
            },
    }
}

# LDAP stuff
AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName", 
    "last_name": "sn",
    "email": "mail"
    }

# App stuff
INTERNAL_IPS = ('127.0.0.1',)

CRISPY_TEMPLATE_PACK = 'bootstrap'

import logging

logger = logging.getLogger('django_auth_ldap')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

# Broker setup
BROKER_URL = 'django://'

CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
CELERYBEAT_PIDFILE = '/tmp/celerybeat.pid'

# CELERY tasks
CELERY_IMPORTS=(
    'articleflow.daemons.em_sync',
    'articleflow.daemons.transition_tasks',
    'articleflow.daemons.merops_tasks',
)

# CELERY beat schedule
CELERYBEAT_SCHEDULE = {
    'em-sync': {
        'task': 'articleflow.daemons.em_sync.sync_all_pubdates',
        'schedule': crontab(hour="*/2", minute="0", day_of_week="*")
        },
    'sync-most-recent-em-changes': {
        'task': 'articleflow.daemons.em_sync.sync_most_recent_em_changes',
        'schedule': timedelta(minutes=1)
        },
    'transitions-tasks': {
        'task': 'articleflow.daemons.transition_tasks.ongoing_ambra_sync',
        'schedule': timedelta(seconds=30)
        },
    'merops-tasks-watch-docs-from-aries': {
        'task': 'articleflow.daemons.merops_tasks.watch_docs_from_aries',
        'schedule': timedelta(seconds=30)
        },
    'merops-tasks-watch-merops-output': {
        'task': 'articleflow.daemons.merops_tasks.watch_merops_output',
        'schedule': timedelta(seconds=30)
        },
    'merops-tasks-move-to-pm': {
        'task': 'articleflow.daemons.merops_tasks.move_to_pm',
        'schedule': timedelta(seconds=30)
        },
    'merops-tasks-watch-finishxml-output': {
        'task': 'articleflow.daemons.merops_tasks.watch_finishxml_output',
        'schedule': timedelta(seconds=30)
        },
    'merops-tasks-build-merops-packages': {
        'task': 'articleflow.daemons.merops_tasks.build_merops_packages',
        'schedule': crontab(minute="*/15", day_of_week="*")
        },
    }



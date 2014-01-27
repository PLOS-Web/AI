# Fill me out and copy me to local_settings.py
#  Things that are necessary for the operation of the base web 
#  server are marked, **REQUIRED**.
#  (then don't ever commit me)

import os
import ldap
import sys
from django_auth_ldap.config import LDAPSearch

"""
 DEBUG=True will show useful 500 traces and stuff
"""
DEBUG = True
TEMPLATE_DEBUG = DEBUG

"""
 **REQUIRED**
   Be sure to create this directory first
"""
LOG_FILE_DIRECTORY = os.path.dirname("/home/jlabarba/ai-logs/")

"""
 Admin Email Accounts
  Needs smtp info to work (at bottom
  email to send 500 stack traces to
  DOESN'T affect any user accounts
"""
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

"""
 Backend Database
  Leave alone to use a crummy sqlite backend.
  HOWEVER, if you plan on doing a full load of production data
  you'll need to create and use a mysql db instead.
  for more info, see 
    https://docs.djangoproject.com/en/dev/intro/tutorial01/#database-setup
"""
DATABASES = {
    # AI backend
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'crummy_db.sqlite',
    }
}

if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test_db'
        }
    SOUTH_TESTS_MIGRATE = False

"""    
 only required for scheduler tasks
  Settings for the EM reporting datasource
"""
EM_REPORTING_DATABASE = {
    'USER': '',
    'PASSWORD': '',
    'HOST': '',
    'PORT': '',
}

"""
 only required for scheduler tasks
"""
AMBRA_STAGE_DATABASE = {
    'USER': '',
    'PASSWORD': '',
    'HOST': '',
    'PORT': 1337,
    'NAME': '',
}

"""
 only required for scheduler tasks
"""
AMBRA_PROD_DATABASE = {
    'USER': '',
    'PASSWORD': '',
    'HOST': '',
    'PORT': 1337,
    'NAME': '',
}

"""
 generate one here and paste in
   http://www.miniwebtool.com/django-secret-key-generator/
"""
SECRET_KEY = ''

"""
 LDAP config
  Requried if you want login authentication to understand plos
  usernames and passwords
"""
AUTH_LDAP_SERVER_URI = ''
AUTH_LDAP_BIND_DN = ''
AUTH_LDAP_BIND_PASSWORD = ''
AUTH_LDAP_USER_SEARCH = LDAPSearch("OU=PLoS,DC=plos,DC=org",
    ldap.SCOPE_SUBTREE, "(sAMAccountName=%(user)s)")

"""
 SMTP
   required if you want to test email notifications 
"""
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''


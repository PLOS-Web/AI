# Fill me out and copy me to local_settings.py
#  (then don't ever commit me)

import ldap
import sys
from django_auth_ldap.config import LDAPSearch

# email to send 500 stack traces to
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

DATABASES = {
    # AI backend
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test_db'
        }
    
# Settings for the EM reporting datasource
EM_REPORTING_DATABASE = {
    'USER': '',
    'PASSWORD': '',
    'HOST': '',
    'PORT': '',
}

# generate one here 
# http://www.miniwebtool.com/django-secret-key-generator/
SECRET_KEY = ''

# LDAP config
AUTH_LDAP_SERVER_URI = ''
AUTH_LDAP_BIND_DN = ''
AUTH_LDAP_BIND_PASSWORD = ''
AUTH_LDAP_USER_SEARCH = LDAPSearch("OU=PLoS,DC=plos,DC=org",
    ldap.SCOPE_SUBTREE, "(sAMAccountName=%(user)s)")

# debug dispatch email config
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''


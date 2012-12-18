from django.conf.urls import patterns, include, url
from errors.views import *

urlpatterns = patterns('errors.views',
                       url(
        r'^(?P<doi>[a-z|\.|0-9]{0,50})/$',
        Errors.as_view(),
        name='article_errors'),
                       url(
        r'^error_status/$',
        'toggle_error_status',
        name='toggle_error_status'),
                       )

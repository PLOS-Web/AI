from django.conf.urls import patterns, include, url
from fancyauth.views import *

urlpatterns = patterns('fancyauth.views',
                       url(r'^login/$', 'loginajax', name='ajax_login'),
                       url(r'^logout/$', 'logoutajax', name='ajax_logout'),
)

from django.conf.urls import patterns, include, url
from articleflow.views import *

urlpatterns = patterns('articleflow.views',
                       url(r'^article/$', PutArticle.as_view(), name='grid'),
                       )

from django.conf.urls import patterns, include, url
from articleflow.views import *

urlpatterns = patterns('articleflow.views',
                       url(r'^article/(?P<doi>[a-z|\.|0-9]{0,50})$', PutArticle.as_view(), name='grid'),
                       )

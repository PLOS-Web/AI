from django.conf.urls import patterns, include, url
from articleflow.views import *

urlpatterns = patterns('articleflow.views',
                       url(r'^article/(?P<doi>[a-z|\.|0-9]{0,50})$', TransactionArticle.as_view(), name='api_article'),
                       url(r'^article/(?P<doi>[a-z|\.|0-9]{0,50})/errorset/(?P<errorset_pk>[0-9]{0,50})$', TransactionErrorset.as_view(), name='api_errorset'),
                       url(r'^article/(?P<doi>[a-z|\.|0-9]{0,50})/transition/$', TransactionTransition.as_view(), name='api_transition'),
                       )

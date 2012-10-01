from django.conf.urls import patterns, include, url
from articleflow.views import ArticleGrid, ArticleDetailTransition

urlpatterns = patterns('articleflow.views',
                       url(r'^grid/$', ArticleGrid.as_view(), name='grid'),
                       url(r'^detail/(?P<doi>[a-z|\.|0-9]{0,50})/$', ArticleDetailTransition.as_view(), name='detail')
                       )
#url(r'^detail/(?P<doi>\w{0,50})$', 'detail', name='detail')

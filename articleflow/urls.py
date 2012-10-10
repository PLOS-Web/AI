from django.conf.urls import patterns, include, url
from articleflow.views import ArticleGrid, ArticleDetailMain, ArticleDetailTransition

urlpatterns = patterns('articleflow.views',
                       url(r'^grid/$', ArticleGrid.as_view(), name='grid'),
                       url(r'^detail/(?P<doi>[a-z|\.|0-9]{0,50})/$', ArticleDetailMain.as_view(), name='detail_main'),
                       url(r'^detail/(?P<doi>[a-z|\.|0-9]{0,50})/transitions', ArticleDetailTransition.as_view(), name='detail_transition')
                       )
#url(r'^detail/(?P<doi>\w{0,50})$', 'detail', name='detail')

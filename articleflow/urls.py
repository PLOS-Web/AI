from django.conf.urls import patterns, include, url
from articleflow.views import ArticleGrid, ArticleDetail

urlpatterns = patterns('articleflow.views',
                       url(r'^grid/$', ArticleGrid.as_view(), name='grid'),
                       url(r'^detail/(?P<slug>[a-z|\.|0-9]{0,50})/$', ArticleDetail.as_view(), name='detail')
                       )
#url(r'^detail/(?P<doi>\w{0,50})$', 'detail', name='detail')

from django.conf.urls import patterns, include, url

urlpatterns = patterns('articleflow.views',
                       url(r'^grid/$', 'grid', name='grid'),
                       url(r'^detail/(?P<doi>\w{0,50})/$', 'detail', name='detail')
                       )
#url(r'^detail/(?P<doi>\w{0,50})$', 'detail', name='detail')

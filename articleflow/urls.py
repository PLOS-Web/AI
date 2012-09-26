from django.conf.urls import patterns, include, url

urlpatterns = patterns('articleflow.views',
    url(r'^grid', 'grid', name='grid'),
)

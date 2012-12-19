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
                       url(
        r'^comments/(?P<id>\d+)$',
        'comment_list',
        name='render_error_comment_list'),
                       url(
        r'^commentblock/(?P<pk>\d+)$',
        'comment_block',
        name='render_error_comment_block'
        ),
                       )

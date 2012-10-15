from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'issues.views',
    url(
        r'^comments/(?P<id>\d+)$',
        'comment_list',
        name='render_comment_list'
    ),
)

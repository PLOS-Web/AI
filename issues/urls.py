from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'issues.views',
    url(
        r'^comments/(?P<id>\d+)$',
        'comment_list',
        name='render_issue_comment_list'),
    url(
        r'^commentblock/(?P<pk>\d+)$',
        'comment_block',
        name='render_issue_comment_block'
    ),
    url(
        r'^post_issue/$',
        'post_issue',
        name='post_issue_ajax'),
)

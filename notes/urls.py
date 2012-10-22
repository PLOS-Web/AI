from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'notes.views',
    url(
        r'^(?P<id>\d+)/list$',
        'note_list',
        name='render_article_note_list'),
    url(
        r'^(?P<pk>\d+)$',
        'note_block',
        name='render_article_note_block'
    ),
)
